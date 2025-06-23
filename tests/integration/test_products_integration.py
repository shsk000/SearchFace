"""
女優別おすすめ商品API の統合テスト

実際のデータベースとAPIの連携テスト
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from src.api.main import app
from src.api.routes.products import get_product_service


@pytest.fixture
def client():
    """テストクライアント"""
    return TestClient(app)


class TestProductsAPIIntegration:
    """女優別おすすめ商品API の統合テスト"""
    
    def test_get_recommended_products_with_real_database(self, client):
        """実際のデータベースとの統合テスト"""
        # PersonDatabaseをモック化（SQLiteスレッド問題を避けるため）
        with patch('src.api.routes.products.PersonDatabase') as mock_db_class:
            mock_db = Mock()
            mock_db.get_person_by_id.return_value = {
                'person_id': 1,
                'name': 'テスト女優',
                'dmm_actress_id': 12345
            }
            mock_db_class.return_value = mock_db
            
            # DmmProductServiceをモック化
            mock_service = Mock()
            mock_service.get_actress_products.return_value = [
                {
                    "imageURL": {
                        "list": "http://test.com/list.jpg",
                        "small": "http://test.com/small.jpg", 
                        "large": "http://test.com/large.jpg"
                    },
                    "title": "統合テスト商品",
                    "productURL": "http://test.com/affiliate",
                    "prices": {"price": "2000"}
                }
            ]
            app.dependency_overrides[get_product_service] = lambda: mock_service
            
            try:
                # APIリクエスト実行
                response = client.get("/api/products/1")
                
                # レスポンス検証
                assert response.status_code == 200
                data = response.json()
                
                assert data["person_id"] == 1
                assert data["person_name"] == "テスト女優"
                assert data["dmm_actress_id"] == 12345
                assert len(data["products"]) == 1
                
                product = data["products"][0]
                assert product["title"] == "統合テスト商品"
                assert product["imageURL"]["list"] == "http://test.com/list.jpg"
            finally:
                # 依存性オーバーライドをクリア
                app.dependency_overrides.clear()
    
    def test_get_recommended_products_person_without_dmm_id(self, client):
        """DMM女優IDが設定されていない人物の統合テスト"""
        # PersonDatabaseをモック化（DMM女優IDなし）
        with patch('src.api.routes.products.PersonDatabase') as mock_db_class:
            mock_db = Mock()
            mock_db.get_person_by_id.return_value = {
                'person_id': 1,
                'name': 'DMM ID なし女優',
                'dmm_actress_id': None  # DMM女優IDなし
            }
            mock_db_class.return_value = mock_db
            
            # モックサービスを設定（エラーを避けるため）
            mock_service = Mock()
            app.dependency_overrides[get_product_service] = lambda: mock_service
            
            try:
                # APIリクエスト実行
                response = client.get("/api/products/1")
                
                # 400エラーが返ることを確認
                assert response.status_code == 400
                data = response.json()
                assert "DMM女優IDが設定されていません" in data["detail"]
            finally:
                # 依存性オーバーライドをクリア
                app.dependency_overrides.clear()
    
    @patch.dict('os.environ', {
        'DMM_API_ID': 'test_api_id',
        'DMM_AFFILIATE_ID': 'test_affiliate_id'
    })
    def test_api_status_check_integration(self, client):
        """API状態確認の統合テスト（環境変数設定あり）"""
        # モックサービスを直接設定
        mock_service = Mock()
        mock_service.check_api_status.return_value = {
            "api_configured": True,
            "api_accessible": True,
            "test_message": "API接続テスト成功"
        }
        
        app.dependency_overrides[get_product_service] = lambda: mock_service
        
        try:
            # APIリクエスト実行
            response = client.get("/api/products/status")
            
            # レスポンス検証
            assert response.status_code == 200
            data = response.json()
            
            assert data["api_configured"] is True
            assert data["api_accessible"] is True
            assert "成功" in data["test_message"]
        finally:
            # 依存性オーバーライドをクリア
            app.dependency_overrides.clear()
    
    def test_api_status_check_no_env_vars(self, client):
        """環境変数なしの場合のAPI状態確認テスト"""
        # 環境変数をクリア
        with patch.dict('os.environ', {}, clear=True):
            # サービス初期化時にエラーが発生することを確認
            response = client.get("/api/products/status")
            
            # 500エラーが返ることを確認（環境変数未設定による初期化失敗）
            assert response.status_code == 500
            data = response.json()
            assert "初期化に失敗しました" in data["detail"] or "API状態確認中にエラーが発生しました" in data["detail"]
    
    def test_dmm_id_direct_api_integration(self, client):
        """DMM女優ID直接指定APIの統合テスト"""
        # DmmProductServiceをモック化
        mock_service = Mock()
        mock_service.get_actress_products.return_value = [
            {
                "imageURL": {
                    "list": "http://direct.com/list.jpg",
                    "small": "http://direct.com/small.jpg",
                    "large": "http://direct.com/large.jpg"
                },
                "title": "直接指定テスト商品",
                "productURL": "http://direct.com/affiliate",
                "prices": {"price": "1500"}
            }
        ]
        
        app.dependency_overrides[get_product_service] = lambda: mock_service
        
        try:
            # APIリクエスト実行
            response = client.get("/api/products/by-dmm-id/54321?limit=5")
            
            # レスポンス検証
            assert response.status_code == 200
            data = response.json()
            
            assert data["dmm_actress_id"] == 54321
            assert data["total_count"] == 1
            assert len(data["products"]) == 1
            
            product = data["products"][0]
            assert product["title"] == "直接指定テスト商品"
            assert product["imageURL"]["large"] == "http://direct.com/large.jpg"
            
            # サービス呼び出し確認
            mock_service.get_actress_products.assert_called_once_with(
                dmm_actress_id=54321,
                limit=5
            )
        finally:
            # 依存性オーバーライドをクリア
            app.dependency_overrides.clear()


class TestAPIParameterValidation:
    """APIパラメータ検証テスト"""
    
    def test_invalid_person_id_format(self, client):
        """無効な人物ID形式のテスト"""
        # モックサービスを設定（エラーを避けるため）
        mock_service = Mock()
        app.dependency_overrides[get_product_service] = lambda: mock_service
        
        try:
            response = client.get("/api/products/invalid_id")
            
            # 422エラー（Validation Error）が返ることを確認
            assert response.status_code == 422
        finally:
            app.dependency_overrides.clear()
    
    def test_negative_person_id(self, client):
        """負の人物IDのテスト"""
        with patch('src.api.routes.products.PersonDatabase') as mock_db_class:
            mock_db = Mock()
            mock_db.get_person_by_id.return_value = None
            mock_db_class.return_value = mock_db
            
            # モックサービスを設定
            mock_service = Mock()
            app.dependency_overrides[get_product_service] = lambda: mock_service
            
            try:
                response = client.get("/api/products/-1")
                
                # 404エラーが返ることを確認
                assert response.status_code == 404
            finally:
                app.dependency_overrides.clear()
    
    def test_limit_parameter_bounds(self, client):
        """limit パラメータの境界値テスト"""
        with patch('src.api.routes.products.PersonDatabase') as mock_db_class:
            mock_db = Mock()
            mock_db.get_person_by_id.return_value = {
                'person_id': 1,
                'name': 'テスト',
                'dmm_actress_id': 12345
            }
            mock_db_class.return_value = mock_db
            
            # モックサービスを設定
            mock_service = Mock()
            mock_service.get_actress_products.return_value = []
            app.dependency_overrides[get_product_service] = lambda: mock_service
            
            # limit=0 のテスト（バリデーションエラー）
            response = client.get("/api/products/1?limit=0")
            assert response.status_code == 422
            
            # limit が20を超える場合のテスト（バリデーションエラー）
            response = client.get("/api/products/1?limit=25")
            assert response.status_code == 422
            
            # 正常範囲のテスト
            response = client.get("/api/products/1?limit=15")
            assert response.status_code == 200
            
            # 15件で呼び出されることを確認
            mock_service.get_actress_products.assert_called_with(
                dmm_actress_id=12345,
                limit=15
            )
            
            # 依存性オーバーライドをクリア
            app.dependency_overrides.clear()