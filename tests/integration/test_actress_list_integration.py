import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
try:
    from fastapi.testclient import TestClient
except ImportError:
    from starlette.testclient import TestClient

from src.api.main import app
from tests.utils.database_test_utils import isolated_test_database, create_test_person_data


class TestActressListIntegration:
    """女優一覧機能の統合テストクラス"""

    @pytest.fixture
    def client(self):
        """Test client fixture"""
        try:
            return TestClient(app)
        except TypeError:
            import httpx
            return httpx.Client(app=app, base_url="http://testserver")

    @pytest.fixture
    def mock_person_database(self):
        """PersonDatabaseのモックを作成"""
        with patch('src.api.routes.persons.PersonDatabase') as mock_person_db_class:
            # モックインスタンス
            mock_person_db = MagicMock()
            mock_person_db_class.return_value = mock_person_db
            
            yield mock_person_db

    def test_actress_list_api_integration_basic(self, client, mock_person_database):
        """基本的な女優一覧APIの統合テスト"""
        mock_person_db = mock_person_database
        
        # テストデータを準備
        test_actresses = [
            {
                'person_id': 1,
                'name': 'AIKA',
                'base_image_path': 'http://pics.dmm.co.jp/mono/actjpgs/aika3.jpg',
                'dmm_actress_id': 1008887
            },
            {
                'person_id': 2,
                'name': 'AIKA（三浦あいか）',
                'base_image_path': 'http://pics.dmm.co.jp/mono/actjpgs/miura_aika.jpg',
                'dmm_actress_id': 1105
            },
            {
                'person_id': 3,
                'name': '愛上みお',
                'base_image_path': 'http://pics.dmm.co.jp/mono/actjpgs/aiue_mio.jpg',
                'dmm_actress_id': 1075314
            }
        ]
        
        mock_person_db.get_persons_list.return_value = test_actresses
        mock_person_db.get_persons_count.return_value = 3

        # APIリクエスト実行
        response = client.get("/api/persons?limit=10&offset=0&sort_by=name")

        # レスポンス検証
        assert response.status_code == 200
        data = response.json()
        
        # 基本構造の確認
        assert 'persons' in data
        assert 'total_count' in data
        assert 'has_more' in data
        
        # データ内容の確認
        assert len(data['persons']) == 3
        assert data['total_count'] == 3
        assert data['has_more'] == False
        
        # 個別の女優データ確認
        aika = data['persons'][0]
        assert aika['person_id'] == 1
        assert aika['name'] == 'AIKA'
        assert aika['image_path'] == 'http://pics.dmm.co.jp/mono/actjpgs/aika3.jpg'
        assert aika['dmm_actress_id'] == 1008887

        # モック呼び出し確認
        mock_person_db.get_persons_list.assert_called_once_with(
            limit=10,
            offset=0,
            search=None,
            sort_by="name"
        )
        mock_person_db.get_persons_count.assert_called_once_with(search=None)
        mock_person_db.close.assert_called_once()

    def test_actress_list_api_integration_with_search(self, client, mock_person_database):
        """検索機能付き女優一覧APIの統合テスト"""
        mock_person_db = mock_person_database
        
        # 検索結果のテストデータ
        search_results = [
            {
                'person_id': 1,
                'name': 'AIKA',
                'base_image_path': 'http://pics.dmm.co.jp/mono/actjpgs/aika3.jpg',
                'dmm_actress_id': 1008887
            },
            {
                'person_id': 2,
                'name': 'AIKA（三浦あいか）',
                'base_image_path': 'http://pics.dmm.co.jp/mono/actjpgs/miura_aika.jpg',
                'dmm_actress_id': 1105
            }
        ]
        
        mock_person_db.get_persons_list.return_value = search_results
        mock_person_db.get_persons_count.return_value = 2

        # 検索APIリクエスト実行
        response = client.get("/api/persons?search=AIKA&limit=20&sort_by=name")

        # レスポンス検証
        assert response.status_code == 200
        data = response.json()
        
        assert len(data['persons']) == 2
        assert data['total_count'] == 2
        
        # 検索結果の確認（すべてAIKAを含む）
        for person in data['persons']:
            assert 'AIKA' in person['name']

        # モック呼び出し確認（検索パラメータ付き）
        mock_person_db.get_persons_list.assert_called_once_with(
            limit=20,
            offset=0,
            search="AIKA",
            sort_by="name"
        )
        mock_person_db.get_persons_count.assert_called_once_with(search="AIKA")

    def test_actress_list_api_integration_pagination(self, client, mock_person_database):
        """ページネーション機能の統合テスト"""
        mock_person_db = mock_person_database
        
        # 2ページ目のデータ
        page2_data = [
            {
                'person_id': 21,
                'name': 'テスト女優21',
                'base_image_path': 'http://example.com/test21.jpg',
                'dmm_actress_id': 21
            }
        ]
        
        mock_person_db.get_persons_list.return_value = page2_data
        mock_person_db.get_persons_count.return_value = 100  # 総数100件

        # 2ページ目のAPIリクエスト
        response = client.get("/api/persons?limit=20&offset=20")

        # レスポンス検証
        assert response.status_code == 200
        data = response.json()
        
        assert len(data['persons']) == 1
        assert data['total_count'] == 100
        assert data['has_more'] == True  # まだデータがある

        # モック呼び出し確認（ページネーション）
        mock_person_db.get_persons_list.assert_called_once_with(
            limit=20,
            offset=20,
            search=None,
            sort_by="name"
        )

    def test_actress_list_api_integration_with_real_database(self, client):
        """実際のデータベースを使用した統合テスト"""
        with isolated_test_database() as (conn, db_path):
            # テストデータを作成
            person1_id = create_test_person_data(conn, "テスト女優1", "http://example.com/test1.jpg")
            person2_id = create_test_person_data(conn, "テスト女優2", "http://example.com/test2.jpg")
            person3_id = create_test_person_data(conn, "AIKA", "http://example.com/aika.jpg")
            
            # DMM IDを追加
            conn.execute(
                "UPDATE persons SET dmm_actress_id = ? WHERE person_id = ?",
                (12345, person1_id)
            )
            conn.execute(
                "UPDATE persons SET dmm_actress_id = ? WHERE person_id = ?",
                (1008887, person3_id)
            )
            conn.commit()

            # データベースパスをモック
            with patch('src.database.person_database.PersonDatabase.DB_PATH', db_path):
                # APIリクエスト実行
                response = client.get("/api/persons?limit=10&sort_by=name")
                
                # レスポンス検証
                assert response.status_code == 200
                data = response.json()
                
                assert len(data['persons']) == 3
                assert data['total_count'] == 3
                
                # 名前順でソートされていることを確認
                names = [person['name'] for person in data['persons']]
                assert names == sorted(names)
                
                # DMM IDが正しく取得されることを確認
                aika_person = next(p for p in data['persons'] if p['name'] == 'AIKA')
                assert aika_person['dmm_actress_id'] == 1008887

    def test_actress_list_api_integration_search_with_real_database(self, client):
        """実際のデータベースを使用した検索機能の統合テスト"""
        with isolated_test_database() as (conn, db_path):
            # テストデータを作成
            create_test_person_data(conn, "AIKA", "http://example.com/aika.jpg")
            create_test_person_data(conn, "AIKA（三浦あいか）", "http://example.com/aika2.jpg")
            create_test_person_data(conn, "愛上みお", "http://example.com/aiue_mio.jpg")
            create_test_person_data(conn, "藍芽みずき", "http://example.com/aiga_mizuki.jpg")

            # データベースパスをモック
            with patch('src.database.person_database.PersonDatabase.DB_PATH', db_path):
                # "AIKA"で検索
                response = client.get("/api/persons?search=AIKA&limit=10")
                
                # レスポンス検証
                assert response.status_code == 200
                data = response.json()
                
                # AIKAを含む2件のみが返されることを確認
                assert len(data['persons']) == 2
                assert data['total_count'] == 2
                
                for person in data['persons']:
                    assert 'AIKA' in person['name']

    def test_actress_list_api_integration_error_handling(self, client):
        """エラーハンドリングの統合テスト"""
        # データベース接続エラーをシミュレート
        with patch('src.api.routes.persons.PersonDatabase') as mock_person_db_class:
            mock_person_db_class.side_effect = Exception("Database connection failed")
            
            response = client.get("/api/persons")
            
            # エラーレスポンス確認
            assert response.status_code == 500
            data = response.json()
            assert "人物一覧の取得中にエラーが発生しました" in data['detail']

    def test_actress_list_api_integration_parameter_validation(self, client):
        """パラメータバリデーションの統合テスト"""
        # 無効なlimitパラメータ
        response = client.get("/api/persons?limit=200")  # 上限超過
        assert response.status_code == 422
        
        # 無効なoffsetパラメータ
        response = client.get("/api/persons?offset=-5")  # 負の値
        assert response.status_code == 422
        
        # 無効なsort_byパラメータ
        response = client.get("/api/persons?sort_by=invalid_column")
        assert response.status_code == 422

    def test_actress_list_api_integration_empty_result(self, client):
        """空の結果の統合テスト"""
        with isolated_test_database() as (conn, db_path):
            # データを作成しない（空のデータベース）
            
            with patch('src.database.person_database.PersonDatabase.DB_PATH', db_path):
                response = client.get("/api/persons")
                
                # 空の結果確認
                assert response.status_code == 200
                data = response.json()
                
                assert data['persons'] == []
                assert data['total_count'] == 0
                assert data['has_more'] == False

    def test_actress_list_api_integration_large_dataset_performance(self, client):
        """大量データでのパフォーマンステスト"""
        with isolated_test_database() as (conn, db_path):
            # 100件のテストデータを作成
            for i in range(100):
                create_test_person_data(conn, f"テスト女優{i:03d}", f"http://example.com/test{i}.jpg")

            with patch('src.database.person_database.PersonDatabase.DB_PATH', db_path):
                # 各ページでのパフォーマンス確認
                import time
                
                # 1ページ目
                start_time = time.time()
                response = client.get("/api/persons?limit=20&offset=0")
                response_time = time.time() - start_time
                
                assert response.status_code == 200
                assert response_time < 1.0  # 1秒以内
                
                data = response.json()
                assert len(data['persons']) == 20
                assert data['total_count'] == 100
                assert data['has_more'] == True
                
                # 最後のページ
                response = client.get("/api/persons?limit=20&offset=80")
                assert response.status_code == 200
                
                data = response.json()
                assert len(data['persons']) == 20
                assert data['has_more'] == False

    def test_actress_list_full_stack_simulation(self, client):
        """フルスタック動作のシミュレーションテスト"""
        with isolated_test_database() as (conn, db_path):
            # 実際のデータに近いテストデータを作成
            actresses_data = [
                ("@YOU", "http://pics.dmm.co.jp/mono/actjpgs/@you.jpg", 12440),
                ("AIKA", "http://pics.dmm.co.jp/mono/actjpgs/aika3.jpg", 1008887),
                ("AIKA（三浦あいか）", "http://pics.dmm.co.jp/mono/actjpgs/miura_aika.jpg", 1105),
                ("愛上みお", "http://pics.dmm.co.jp/mono/actjpgs/aiue_mio.jpg", 1075314),
                ("藍芽みずき", "http://pics.dmm.co.jp/mono/actjpgs/aiga_mizuki.jpg", 1055230)
            ]
            
            for name, image_path, dmm_id in actresses_data:
                person_id = create_test_person_data(conn, name, image_path)
                conn.execute(
                    "UPDATE persons SET dmm_actress_id = ? WHERE person_id = ?",
                    (dmm_id, person_id)
                )
            conn.commit()

            with patch('src.database.person_database.PersonDatabase.DB_PATH', db_path):
                # 1. 初期ページロード
                response = client.get("/api/persons?limit=20")
                assert response.status_code == 200
                data = response.json()
                assert len(data['persons']) == 5
                assert data['total_count'] == 5
                
                # 2. 検索実行
                response = client.get("/api/persons?search=AIKA&limit=20")
                assert response.status_code == 200
                data = response.json()
                assert len(data['persons']) == 2
                
                # 3. ソート変更
                response = client.get("/api/persons?sort_by=person_id&limit=20")
                assert response.status_code == 200
                data = response.json()
                # person_id順になっていることを確認
                ids = [person['person_id'] for person in data['persons']]
                assert ids == sorted(ids)
                
                # 4. 個別女優詳細へのアクセス（既存エンドポイント）
                first_person_id = data['persons'][0]['person_id']
                
                # 女優詳細APIはFaceDatabaseを使用するため、モックで対応
                with patch('src.api.routes.persons.FaceDatabase') as mock_face_db_class:
                    with patch('src.api.routes.persons.RankingDatabase') as mock_ranking_db_class:
                        # FaceDatabaseのモック設定
                        mock_face_db = MagicMock()
                        mock_face_db_class.return_value = mock_face_db
                        mock_face_db.get_person_detail.return_value = {
                            'person_id': first_person_id,
                            'name': '@YOU',
                            'base_image_path': 'http://pics.dmm.co.jp/mono/actjpgs/@you.jpg'
                        }
                        
                        # RankingDatabaseのモック設定
                        mock_ranking_db = MagicMock()
                        mock_ranking_db_class.return_value = mock_ranking_db
                        mock_ranking_db.get_person_search_count.return_value = 42
                        
                        response = client.get(f"/api/persons/{first_person_id}")
                        assert response.status_code == 200
                        detail_data = response.json()
                        assert detail_data['person_id'] == first_person_id
                        assert detail_data['search_count'] == 42