import pytest
import tempfile
import os
import numpy as np
from unittest.mock import patch, MagicMock
from src.database.face_index_database import FaceIndexDatabase
from src.database.person_database import PersonDatabase
from tests.utils.database_test_utils import isolated_test_database, create_test_person_data, create_test_database_with_schema


class TestFaceIndexDatabase:
    """FaceIndexDatabase クラスのテストクラス"""

    @pytest.fixture
    def temp_paths(self):
        """テスト用の一時ファイルパスを作成"""
        # データベースファイル
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
            db_path = temp_db.name
        
        # インデックスファイル
        with tempfile.NamedTemporaryFile(suffix='.index', delete=False) as temp_index:
            index_path = temp_index.name
        
        yield db_path, index_path
        
        # クリーンアップ
        for path in [db_path, index_path]:
            if os.path.exists(path):
                os.unlink(path)

    @pytest.fixture
    def setup_person_data(self, temp_paths):
        """テスト用の人物データをセットアップ - SAFE: Uses utility for schema setup"""
        db_path, index_path = temp_paths
        
        # Create database with proper schema from sqlite_schema.sql (SAFE: single source of truth)
        conn, temp_schema_path = create_test_database_with_schema()
        conn.close()
        
        # Move to expected test path
        import shutil
        shutil.move(temp_schema_path, db_path)
        
        # Reopen with expected path and Row factory
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # Create test person data (SAFE: temporary path only)
        person_id = create_test_person_data(
            conn, 
            person_name="テスト人物",
            base_image_path="/tmp/test_image_path.jpg"  # SAFE: temporary path
        )
        conn.close()
        
        return db_path, index_path, person_id

    @pytest.fixture
    def face_index_db(self, setup_person_data):
        """FaceIndexDatabase インスタンスを作成"""
        db_path, index_path, person_id = setup_person_data
        
        with patch('src.face.face_utils.get_face_encoding') as mock_get_encoding, \
             patch('src.database.face_index_database.FaceIndexDatabase._verify_tables_exist'), \
             patch('src.database.face_index_database.FaceIndexDatabase._load_index'), \
             patch('src.database.face_index_database.faiss') as mock_faiss:
            # モックの設定
            mock_get_encoding.return_value = None  # 空のインデックスを作成
            mock_index = MagicMock()
            mock_index.ntotal = 0
            
            # Mock the add method to increment ntotal
            def mock_add(vectors):
                current_total = mock_index.ntotal
                mock_index.ntotal = current_total + vectors.shape[0]
            
            # Mock the search method to return proper tuple
            def mock_search(query_vectors, k):
                import numpy as np
                # Return empty results for empty index
                if mock_index.ntotal == 0:
                    return np.array([[]]), np.array([[]])
                # Return mock results for non-empty index
                distances = np.array([[0.1, 0.2, 0.3]])[:, :min(k, mock_index.ntotal)]
                indices = np.array([[0, 1, 2]])[:, :min(k, mock_index.ntotal)]
                return distances, indices
            
            mock_index.add = mock_add
            mock_index.search = mock_search
            mock_faiss.IndexFlatL2.return_value = mock_index
            mock_faiss.read_index.return_value = mock_index
            mock_faiss.write_index.return_value = None  # Mock write_index
            
            db = FaceIndexDatabase(db_path, index_path)
            # Manually set the index since _load_index is mocked
            db.index = mock_index
            yield db, person_id
            db.close()

    def test_initialization(self, temp_paths):
        """初期化のテスト"""
        db_path, index_path = temp_paths
        
        # 人物データを事前に作成
        person_db = PersonDatabase(db_path)
        person_db.create_person("テスト人物")
        person_db.close()
        
        with patch('src.face.face_utils.get_face_encoding') as mock_get_encoding, \
             patch('src.database.face_index_database.FaceIndexDatabase._verify_tables_exist'), \
             patch('src.database.face_index_database.FaceIndexDatabase._load_index'), \
             patch('src.database.face_index_database.faiss') as mock_faiss:
            # Mock settings
            mock_get_encoding.return_value = None
            mock_index = MagicMock()
            mock_index.ntotal = 0
            mock_faiss.IndexFlatL2.return_value = mock_index
            mock_faiss.read_index.return_value = mock_index
            
            db = FaceIndexDatabase(db_path, index_path)
            # Manually set the index since _load_index is mocked
            db.index = mock_index
            
            # インデックスが作成されていることを確認
            assert db.index is not None
            assert db.index.ntotal == 0  # 空のインデックス
            
            db.close()

    def test_add_face_image(self, face_index_db):
        """顔画像追加のテスト"""
        db, person_id = face_index_db
        
        # テストデータ
        image_path = "test/path/image.jpg"
        encoding = np.random.rand(128).astype(np.float32)
        image_hash = "test_hash_123"
        metadata = {"test": "data"}
        
        # 顔画像を追加
        image_id = db.add_face_image(person_id, image_path, encoding, image_hash, metadata)
        
        # 結果を確認
        assert image_id is not None
        assert isinstance(image_id, int)
        assert image_id > 0
        
        # インデックスにも追加されていることを確認
        assert db.index.ntotal == 1

    def test_add_duplicate_face_image(self, face_index_db):
        """重複画像追加のテスト"""
        db, person_id = face_index_db
        
        # テストデータ
        image_path = "test/path/image.jpg"
        encoding = np.random.rand(128).astype(np.float32)
        image_hash = "duplicate_hash"
        
        # 最初の追加
        first_id = db.add_face_image(person_id, image_path, encoding, image_hash)
        
        # 同じハッシュで再度追加（重複）
        second_id = db.add_face_image(person_id, "different/path.jpg", encoding, image_hash)
        
        # 同じIDが返されることを確認
        assert first_id == second_id

    def test_search_similar_faces_empty(self, face_index_db):
        """空のインデックスでの検索テスト"""
        db, person_id = face_index_db
        
        query_encoding = np.random.rand(128).astype(np.float32)
        results = db.search_similar_faces(query_encoding, top_k=5)
        
        # 空の結果が返されることを確認
        assert results == []

    def test_search_similar_faces_with_data(self, face_index_db):
        """データがある状態での検索テスト"""
        db, person_id = face_index_db
        
        # テスト用の顔画像を追加
        encoding1 = np.random.rand(128).astype(np.float32)
        db.add_face_image(person_id, "test1.jpg", encoding1, "hash1")
        
        # 検索実行
        query_encoding = np.random.rand(128).astype(np.float32)
        
        with patch.object(db, 'cursor') as mock_cursor:
            # モックの設定
            mock_cursor.execute.return_value = None
            mock_cursor.fetchone.return_value = {
                'person_id': person_id,
                'name': 'テスト人物',
                'base_image_path': 'data/images/base/テスト人物.jpg',
                'metadata': None
            }
            
            results = db.search_similar_faces(query_encoding, top_k=5)
            
            # 結果の基本構造を確認
            assert isinstance(results, list)

    def test_get_face_image(self, face_index_db):
        """顔画像取得のテスト"""
        db, person_id = face_index_db
        
        # テスト用の顔画像を追加
        image_path = "test/path/image.jpg"
        encoding = np.random.rand(128).astype(np.float32)
        image_hash = "test_hash"
        metadata = {"test": "data"}
        
        image_id = db.add_face_image(person_id, image_path, encoding, image_hash, metadata)
        
        # 画像情報を取得
        face_image = db.get_face_image(image_id)
        
        # 結果を確認
        assert face_image is not None
        assert face_image['image_id'] == image_id
        assert face_image['person_id'] == person_id
        assert face_image['image_path'] == image_path
        assert face_image['image_hash'] == image_hash
        assert face_image['metadata'] == metadata

    def test_get_face_image_not_found(self, face_index_db):
        """存在しない画像の取得テスト"""
        db, person_id = face_index_db
        
        face_image = db.get_face_image(999999)
        assert face_image is None

    def test_get_faces_by_person(self, face_index_db):
        """人物別顔画像取得のテスト"""
        db, person_id = face_index_db
        
        # 複数の顔画像を追加
        images_data = [
            ("image1.jpg", "hash1"),
            ("image2.jpg", "hash2"),
            ("image3.jpg", "hash3")
        ]
        
        added_ids = []
        for image_path, image_hash in images_data:
            encoding = np.random.rand(128).astype(np.float32)
            image_id = db.add_face_image(person_id, image_path, encoding, image_hash)
            added_ids.append(image_id)
        
        # 人物の顔画像一覧を取得
        faces = db.get_faces_by_person(person_id)
        
        # 結果を確認
        assert len(faces) == 3
        retrieved_ids = [face['image_id'] for face in faces]
        assert set(retrieved_ids) == set(added_ids)

    def test_get_all_face_images(self, face_index_db):
        """全顔画像取得のテスト"""
        db, person_id = face_index_db
        
        # 複数の顔画像を追加
        images_count = 3
        for i in range(images_count):
            encoding = np.random.rand(128).astype(np.float32)
            db.add_face_image(person_id, f"image{i}.jpg", encoding, f"hash{i}")
        
        # 全顔画像を取得
        all_faces = db.get_all_face_images()
        
        # 結果を確認
        assert len(all_faces) == images_count
        for face in all_faces:
            assert 'image_id' in face
            assert 'person_id' in face
            assert 'image_path' in face
            assert 'index_position' in face

    def test_delete_face_image(self, face_index_db):
        """顔画像削除のテスト"""
        db, person_id = face_index_db
        
        # 顔画像を追加
        encoding = np.random.rand(128).astype(np.float32)
        image_id = db.add_face_image(person_id, "test.jpg", encoding, "test_hash")
        
        # 削除実行
        success = db.delete_face_image(image_id)
        assert success is True
        
        # 削除されたことを確認
        face_image = db.get_face_image(image_id)
        assert face_image is None

    def test_delete_face_image_not_found(self, face_index_db):
        """存在しない画像の削除テスト"""
        db, person_id = face_index_db
        
        success = db.delete_face_image(999999)
        assert success is False

    def test_get_index_stats(self, face_index_db):
        """インデックス統計取得のテスト"""
        db, person_id = face_index_db
        
        # 初期状態の統計
        stats = db.get_index_stats()
        
        # 基本的な統計情報が含まれることを確認
        assert 'faiss_vector_count' in stats
        assert 'db_image_count' in stats
        assert 'db_index_count' in stats
        assert 'vector_dimension' in stats
        assert 'index_file_exists' in stats
        
        assert stats['faiss_vector_count'] == 0
        assert stats['vector_dimension'] == 128

    def test_index_operations(self, face_index_db):
        """インデックス操作の統合テスト"""
        db, person_id = face_index_db
        
        # 顔画像を追加
        encoding = np.random.rand(128).astype(np.float32)
        image_id = db.add_face_image(person_id, "test.jpg", encoding, "test_hash")
        
        # インデックスが正常に動作することを確認
        assert db.index is not None
        assert db.index.ntotal == 1
        assert image_id > 0