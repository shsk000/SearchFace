import pytest
from unittest.mock import patch, MagicMock
try:
    from fastapi.testclient import TestClient
except ImportError:
    from starlette.testclient import TestClient

from src.api.main import app

class TestPersonsAPI:
    """人物詳細API のテストクラス"""

    @pytest.fixture
    def client(self):
        """Test client fixture"""
        # 互換性の問題を回避するためにより安全なパラメータで初期化
        try:
            return TestClient(app)
        except TypeError:
            # 新しいバージョンのhttpx/starlette用のフォールバック
            import httpx
            from starlette.applications import Starlette
            return httpx.Client(app=app, base_url="http://testserver")

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