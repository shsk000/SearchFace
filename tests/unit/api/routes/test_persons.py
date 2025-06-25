import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from src.api.main import app

class TestPersonsAPI:
    """人物詳細API のテストクラス"""

    @pytest.fixture
    def client(self):
        """Test client fixture"""
        return TestClient(app)

    @patch('src.api.routes.persons.RankingDatabase')
    @patch('src.api.routes.persons.FaceDatabase')
    def test_get_person_detail_success(self, mock_face_db_class, mock_ranking_db_class, client):
        """人物詳細取得の成功ケース"""
        # FaceDatabaseのモックセットアップ
        mock_face_db = MagicMock()
        mock_face_db_class.return_value = mock_face_db
        mock_face_db.get_person_detail.return_value = {
            'person_id': 1,
            'name': 'テスト女優',
            'base_image_path': 'data/images/base/test_actress.jpg'
        }

        # RankingDatabaseのモックセットアップ
        mock_ranking_db = MagicMock()
        mock_ranking_db_class.return_value = mock_ranking_db
        mock_ranking_db.get_person_search_count.return_value = 5

        # APIリクエスト
        response = client.get("/api/persons/1")

        # レスポンス確認
        assert response.status_code == 200
        data = response.json()
        assert data['person_id'] == 1
        assert data['name'] == 'テスト女優'
        assert data['image_path'] == 'data/images/base/test_actress.jpg'
        assert data['search_count'] == 5

        # メソッド呼び出し確認
        mock_face_db.get_person_detail.assert_called_once_with(1)
        mock_ranking_db.get_person_search_count.assert_called_once_with(1)
        mock_face_db.close.assert_called_once()
        mock_ranking_db.close.assert_called_once()

    @patch('src.api.routes.persons.RankingDatabase')
    @patch('src.api.routes.persons.FaceDatabase')
    def test_get_person_detail_not_found(self, mock_face_db_class, mock_ranking_db_class, client):
        """存在しない人物IDの場合のテスト"""
        # FaceDatabaseのモックセットアップ（人物が見つからない）
        mock_face_db = MagicMock()
        mock_face_db_class.return_value = mock_face_db
        mock_face_db.get_person_detail.return_value = None

        # RankingDatabaseのモック
        mock_ranking_db = MagicMock()
        mock_ranking_db_class.return_value = mock_ranking_db

        # APIリクエスト
        response = client.get("/api/persons/999")

        # レスポンス確認
        assert response.status_code == 404
        data = response.json()
        assert "人物ID 999 が見つかりません" in data['detail']

        # メソッド呼び出し確認
        mock_face_db.get_person_detail.assert_called_once_with(999)
        mock_ranking_db.get_person_search_count.assert_not_called()
        mock_face_db.close.assert_called_once()
        # ranking_dbは初期化されていないのでcloseは呼ばれない
        mock_ranking_db.close.assert_not_called()

    @patch('src.api.routes.persons.RankingDatabase')
    @patch('src.api.routes.persons.FaceDatabase')
    def test_get_person_detail_with_none_image_path(self, mock_face_db_class, mock_ranking_db_class, client):
        """画像パスがNoneの場合のテスト"""
        # FaceDatabaseのモックセットアップ
        mock_face_db = MagicMock()
        mock_face_db_class.return_value = mock_face_db
        mock_face_db.get_person_detail.return_value = {
            'person_id': 2,
            'name': 'テスト女優2',
            'base_image_path': None
        }

        # RankingDatabaseのモックセットアップ
        mock_ranking_db = MagicMock()
        mock_ranking_db_class.return_value = mock_ranking_db
        mock_ranking_db.get_person_search_count.return_value = 0

        # APIリクエスト
        response = client.get("/api/persons/2")

        # レスポンス確認
        assert response.status_code == 200
        data = response.json()
        assert data['person_id'] == 2
        assert data['name'] == 'テスト女優2'
        assert data['image_path'] == ""
        assert data['search_count'] == 0

    @patch('src.api.routes.persons.PersonDatabase')
    def test_get_persons_list_success(self, mock_person_db_class, client):
        """人物一覧取得の成功ケース"""
        # PersonDatabaseのモックセットアップ
        mock_person_db = MagicMock()
        mock_person_db_class.return_value = mock_person_db

        # モックデータ
        mock_persons_data = [
            {
                'person_id': 1,
                'name': 'テスト女優1',
                'base_image_path': 'data/images/base/test1.jpg',
                'dmm_actress_id': 12345
            },
            {
                'person_id': 2,
                'name': 'テスト女優2',
                'base_image_path': None,
                'dmm_actress_id': None
            }
        ]

        mock_person_db.get_persons_list.return_value = mock_persons_data
        mock_person_db.get_persons_count.return_value = 2

        # APIリクエスト
        response = client.get("/api/persons?limit=10&offset=0")

        # レスポンス確認
        assert response.status_code == 200
        data = response.json()
        assert len(data['persons']) == 2
        assert data['total_count'] == 2
        assert data['has_more'] == False

        # 最初の人物データ確認
        first_person = data['persons'][0]
        assert first_person['person_id'] == 1
        assert first_person['name'] == 'テスト女優1'
        assert first_person['image_path'] == 'data/images/base/test1.jpg'
        assert first_person['dmm_actress_id'] == 12345

        # 2番目の人物データ確認（null値の処理）
        second_person = data['persons'][1]
        assert second_person['person_id'] == 2
        assert second_person['name'] == 'テスト女優2'
        assert second_person['image_path'] is None
        assert second_person['dmm_actress_id'] is None

        # メソッド呼び出し確認
        mock_person_db.get_persons_list.assert_called_once_with(
            limit=10,
            offset=0,
            search=None,
            sort_by="name"
        )
        mock_person_db.get_persons_count.assert_called_once_with(search=None)
        mock_person_db.close.assert_called_once()

    @patch('src.api.routes.persons.PersonDatabase')
    def test_get_persons_list_with_search(self, mock_person_db_class, client):
        """検索機能付き人物一覧取得のテスト"""
        # PersonDatabaseのモックセットアップ
        mock_person_db = MagicMock()
        mock_person_db_class.return_value = mock_person_db

        # 検索結果のモックデータ
        mock_persons_data = [
            {
                'person_id': 1,
                'name': 'AIKA',
                'base_image_path': 'data/images/base/aika.jpg',
                'dmm_actress_id': 1008887
            }
        ]

        mock_person_db.get_persons_list.return_value = mock_persons_data
        mock_person_db.get_persons_count.return_value = 1

        # 検索パラメータ付きAPIリクエスト
        response = client.get("/api/persons?search=AIKA&limit=20&sort_by=name")

        # レスポンス確認
        assert response.status_code == 200
        data = response.json()
        assert len(data['persons']) == 1
        assert data['total_count'] == 1
        assert data['has_more'] == False

        # 検索結果データ確認
        person = data['persons'][0]
        assert person['name'] == 'AIKA'

        # メソッド呼び出し確認（検索パラメータ含む）
        mock_person_db.get_persons_list.assert_called_once_with(
            limit=20,
            offset=0,
            search="AIKA",
            sort_by="name"
        )
        mock_person_db.get_persons_count.assert_called_once_with(search="AIKA")
        mock_person_db.close.assert_called_once()

    @patch('src.api.routes.persons.PersonDatabase')
    def test_get_persons_list_with_pagination(self, mock_person_db_class, client):
        """ページネーション機能のテスト"""
        # PersonDatabaseのモックセットアップ
        mock_person_db = MagicMock()
        mock_person_db_class.return_value = mock_person_db

        # 2ページ目のデータ（20件目以降）
        mock_persons_data = [
            {
                'person_id': 21,
                'name': 'テスト女優21',
                'base_image_path': 'data/images/base/test21.jpg',
                'dmm_actress_id': 21
            }
        ]

        mock_person_db.get_persons_list.return_value = mock_persons_data
        mock_person_db.get_persons_count.return_value = 100  # 総数100件

        # 2ページ目のAPIリクエスト
        response = client.get("/api/persons?limit=20&offset=20")

        # レスポンス確認
        assert response.status_code == 200
        data = response.json()
        assert len(data['persons']) == 1
        assert data['total_count'] == 100
        assert data['has_more'] == True  # まだデータがあることを確認

        # メソッド呼び出し確認（offset=20）
        mock_person_db.get_persons_list.assert_called_once_with(
            limit=20,
            offset=20,
            search=None,
            sort_by="name"
        )
        mock_person_db.close.assert_called_once()

    @patch('src.api.routes.persons.PersonDatabase')
    def test_get_persons_list_validation_errors(self, mock_person_db_class, client):
        """バリデーションエラーのテスト"""
        # 無効なlimitパラメータ（範囲外）
        response = client.get("/api/persons?limit=150")  # 上限100を超過
        assert response.status_code == 422

        # 無効なoffsetパラメータ（負の値）
        response = client.get("/api/persons?offset=-1")
        assert response.status_code == 422

        # 無効なsort_byパラメータ
        response = client.get("/api/persons?sort_by=invalid_sort")
        assert response.status_code == 422

    @patch('src.api.routes.persons.PersonDatabase')
    def test_get_persons_list_sort_options(self, mock_person_db_class, client):
        """ソート機能のテスト"""
        # PersonDatabaseのモックセットアップ
        mock_person_db = MagicMock()
        mock_person_db_class.return_value = mock_person_db

        mock_person_db.get_persons_list.return_value = []
        mock_person_db.get_persons_count.return_value = 0

        # 各ソートオプションをテスト
        sort_options = ["name", "person_id", "created_at"]

        for sort_by in sort_options:
            response = client.get(f"/api/persons?sort_by={sort_by}")
            assert response.status_code == 200

            # 最後の呼び出しの引数を確認
            args, kwargs = mock_person_db.get_persons_list.call_args
            assert kwargs['sort_by'] == sort_by

    @patch('src.api.routes.persons.PersonDatabase')
    def test_get_persons_list_database_error(self, mock_person_db_class, client):
        """データベースエラーのテスト"""
        # PersonDatabaseのモックセットアップ（エラーを発生させる）
        mock_person_db = MagicMock()
        mock_person_db_class.return_value = mock_person_db
        mock_person_db.get_persons_list.side_effect = Exception("Database connection error")

        # APIリクエスト
        response = client.get("/api/persons")

        # エラーレスポンス確認
        assert response.status_code == 500
        data = response.json()
        assert "人物一覧の取得中にエラーが発生しました" in data['detail']

        # closeメソッドは必ず呼ばれることを確認
        mock_person_db.close.assert_called_once()