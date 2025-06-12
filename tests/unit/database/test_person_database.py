import pytest
import tempfile
import os
from src.database.person_database import PersonDatabase


class TestPersonDatabase:
    """PersonDatabase クラスのテストクラス"""

    @pytest.fixture
    def temp_db_path(self):
        """テスト用の一時データベースファイルパスを作成"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_file:
            temp_path = temp_file.name
        yield temp_path
        # クリーンアップ
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.fixture
    def person_db(self, temp_db_path):
        """PersonDatabase インスタンスを作成"""
        db = PersonDatabase(temp_db_path)
        yield db
        db.close()

    def test_create_person(self, person_db):
        """人物作成のテスト"""
        # テストデータ
        name = "テスト人物"
        metadata = {"test": "data"}
        
        # 人物を作成
        person_id = person_db.create_person(name, metadata)
        
        # 結果を確認
        assert person_id is not None
        assert isinstance(person_id, int)
        assert person_id > 0

    def test_get_person_by_name(self, person_db):
        """名前による人物検索のテスト"""
        # テストデータ
        name = "テスト人物"
        metadata = {"test": "data"}
        
        # 人物を作成
        created_id = person_db.create_person(name, metadata)
        
        # 名前で検索
        person = person_db.get_person_by_name(name)
        
        # 結果を確認
        assert person is not None
        assert person['person_id'] == created_id
        assert person['name'] == name
        assert person['metadata'] == metadata

    def test_get_person_by_name_not_found(self, person_db):
        """存在しない人物名での検索テスト"""
        person = person_db.get_person_by_name("存在しない人物")
        assert person is None

    def test_get_person_by_id(self, person_db):
        """IDによる人物検索のテスト"""
        # テストデータ
        name = "テスト人物"
        metadata = {"test": "data"}
        
        # 人物を作成
        created_id = person_db.create_person(name, metadata)
        
        # IDで検索
        person = person_db.get_person_by_id(created_id)
        
        # 結果を確認
        assert person is not None
        assert person['person_id'] == created_id
        assert person['name'] == name
        assert person['metadata'] == metadata

    def test_get_person_by_id_not_found(self, person_db):
        """存在しない人物IDでの検索テスト"""
        person = person_db.get_person_by_id(999999)
        assert person is None

    def test_get_person_names(self, person_db):
        """複数人物名取得のテスト"""
        # テストデータ
        names = ["人物1", "人物2", "人物3"]
        person_ids = []
        
        # 複数の人物を作成
        for name in names:
            person_id = person_db.create_person(name)
            person_ids.append(person_id)
        
        # 名前を取得
        name_mapping = person_db.get_person_names(person_ids)
        
        # 結果を確認
        assert len(name_mapping) == 3
        for person_id, name in zip(person_ids, names):
            assert name_mapping[person_id] == name

    def test_get_person_names_empty(self, person_db):
        """空のIDリストでの名前取得テスト"""
        name_mapping = person_db.get_person_names([])
        assert name_mapping == {}

    def test_create_person_profile(self, person_db):
        """人物プロフィール作成のテスト"""
        # 人物を作成
        person_id = person_db.create_person("テスト人物")
        
        # プロフィールを作成
        base_image_path = "test/path/image.jpg"
        metadata = {"profile": "test"}
        
        profile_id = person_db.create_person_profile(person_id, base_image_path, metadata)
        
        # 結果を確認
        assert profile_id is not None
        assert isinstance(profile_id, int)
        assert profile_id > 0

    def test_get_person_profile(self, person_db):
        """人物プロフィール取得のテスト"""
        # 人物を作成
        person_id = person_db.create_person("テスト人物")
        
        # プロフィールを作成
        base_image_path = "test/path/image.jpg"
        metadata = {"profile": "test"}
        profile_id = person_db.create_person_profile(person_id, base_image_path, metadata)
        
        # プロフィールを取得
        profile = person_db.get_person_profile(person_id)
        
        # 結果を確認
        assert profile is not None
        assert profile['profile_id'] == profile_id
        assert profile['person_id'] == person_id
        assert profile['base_image_path'] == base_image_path
        assert profile['metadata'] == metadata

    def test_get_person_profile_not_found(self, person_db):
        """存在しない人物のプロフィール取得テスト"""
        profile = person_db.get_person_profile(999999)
        assert profile is None

    def test_get_person_detail(self, person_db):
        """人物詳細情報取得のテスト"""
        # 人物を作成
        name = "テスト人物"
        person_id = person_db.create_person(name)
        
        # プロフィールを作成
        base_image_path = "test/path/image.jpg"
        person_db.create_person_profile(person_id, base_image_path)
        
        # 詳細情報を取得
        detail = person_db.get_person_detail(person_id)
        
        # 結果を確認
        assert detail is not None
        assert detail['person_id'] == person_id
        assert detail['name'] == name
        assert detail['image_path'] == base_image_path

    def test_get_or_create_person_existing(self, person_db):
        """既存人物の取得テスト"""
        # 人物を作成
        name = "テスト人物"
        original_id = person_db.create_person(name)
        
        # 同じ名前で get_or_create を呼び出し
        person_id = person_db.get_or_create_person(name)
        
        # 既存のIDが返されることを確認
        assert person_id == original_id

    def test_get_or_create_person_new(self, person_db):
        """新規人物の作成テスト"""
        # 新しい人物名で get_or_create を呼び出し
        name = "新しい人物"
        metadata = {"new": "person"}
        
        person_id = person_db.get_or_create_person(name, metadata)
        
        # 新しい人物が作成されることを確認
        assert person_id is not None
        
        # 人物情報を確認
        person = person_db.get_person_by_id(person_id)
        assert person['name'] == name
        assert person['metadata'] == metadata
        
        # プロフィールも作成されることを確認
        profile = person_db.get_person_profile(person_id)
        assert profile is not None
        assert profile['base_image_path'] == f"data/images/base/{name}.jpg"

    def test_update_person(self, person_db):
        """人物情報更新のテスト"""
        # 人物を作成
        original_name = "元の名前"
        person_id = person_db.create_person(original_name)
        
        # 情報を更新
        new_name = "新しい名前"
        new_metadata = {"updated": "data"}
        
        success = person_db.update_person(person_id, new_name, new_metadata)
        assert success is True
        
        # 更新された情報を確認
        person = person_db.get_person_by_id(person_id)
        assert person['name'] == new_name
        assert person['metadata'] == new_metadata

    def test_update_person_not_found(self, person_db):
        """存在しない人物の更新テスト"""
        success = person_db.update_person(999999, "新しい名前")
        assert success is False

    def test_delete_person(self, person_db):
        """人物削除のテスト"""
        # 人物を作成
        person_id = person_db.create_person("削除される人物")
        
        # 削除実行
        success = person_db.delete_person(person_id)
        assert success is True
        
        # 削除されたことを確認
        person = person_db.get_person_by_id(person_id)
        assert person is None

    def test_delete_person_not_found(self, person_db):
        """存在しない人物の削除テスト"""
        success = person_db.delete_person(999999)
        assert success is False

    def test_get_all_persons(self, person_db):
        """全人物取得のテスト"""
        # テストデータ
        names = ["人物1", "人物2", "人物3"]
        
        # 複数の人物を作成
        for name in names:
            person_id = person_db.create_person(name)
            # プロフィールも作成
            base_image_path = f"test/path/{name}.jpg"
            person_db.create_person_profile(person_id, base_image_path)
        
        # 全人物を取得
        all_persons = person_db.get_all_persons()
        
        # 結果を確認
        assert len(all_persons) == 3
        retrieved_names = [person['name'] for person in all_persons]
        assert set(retrieved_names) == set(names)
        
        # プロフィール情報も含まれることを確認
        for person in all_persons:
            assert person['base_image_path'] is not None