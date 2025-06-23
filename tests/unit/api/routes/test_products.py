"""
女優別おすすめ商品API関連のテストケース
"""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from src.api.main import app
from src.api.routes.products import get_product_service


class TestRecommendedProductsAPI:
    """女優別おすすめ商品API のテスト"""

    @pytest.fixture
    def client(self):
        """テストクライアント"""
        return TestClient(app)


    @pytest.fixture
    def mock_product_response(self):
        """テスト用の商品レスポンスデータ"""
        return [{
            "imageURL": {
                "list": "http://test.com/list.jpg",
                "small": "http://test.com/small.jpg", 
                "large": "http://test.com/large.jpg"
            },
            "title": "テスト商品",
            "productURL": "http://test.com/affiliate",
            "prices": {"price": "1000"}
        }]
    
    @patch('src.api.routes.products.PersonDatabase')
    def test_get_recommended_products_success(self, mock_db_class, client, mock_product_response):
        """正常な商品取得のテスト"""
        # PersonDatabaseのモック設定
        mock_db = Mock()
        mock_db.get_person_by_id.return_value = {
            'person_id': 1,
            'name': 'テスト女優',
            'dmm_actress_id': 12345
        }
        mock_db_class.return_value = mock_db
        
        # DmmProductServiceのモック設定
        mock_service = Mock()
        mock_service.get_actress_products.return_value = mock_product_response
        
        # FastAPIの依存性注入をオーバーライド
        app.dependency_overrides[get_product_service] = lambda: mock_service
        
        # APIリクエスト実行
        response = client.get("/api/products/1?limit=5")
        
        # レスポンス検証
        assert response.status_code == 200
        data = response.json()
        
        assert data["person_id"] == 1
        assert data["person_name"] == "テスト女優"
        assert data["dmm_actress_id"] == 12345
        assert data["total_count"] == 1
        assert len(data["products"]) == 1
        
        # 商品データ検証
        product = data["products"][0]
        assert product["title"] == "テスト商品"
        assert product["productURL"] == "http://test.com/affiliate"
        assert product["prices"] == {"price": "1000"}
        
        # 画像URL構造検証
        image_urls = product["imageURL"]
        assert image_urls["list"] == "http://test.com/list.jpg"
        assert image_urls["small"] == "http://test.com/small.jpg"
        assert image_urls["large"] == "http://test.com/large.jpg"
        
        # モック呼び出し検証
        mock_db.get_person_by_id.assert_called_once_with(1)
        mock_service.get_actress_products.assert_called_once_with(
            dmm_actress_id=12345,
            limit=5
        )
        
        # 依存性オーバーライドをクリア
        app.dependency_overrides.clear()
    
    @patch('src.api.routes.products.PersonDatabase')
    def test_get_recommended_products_person_not_found(self, mock_db_class, client):
        """存在しない人物IDのテスト"""
        # PersonDatabaseのモック設定（人物が見つからない）
        mock_db = Mock()
        mock_db.get_person_by_id.return_value = None
        mock_db_class.return_value = mock_db
        
        # DmmProductServiceのモック設定（呼び出されないがエラーを避けるため）
        mock_service = Mock()
        app.dependency_overrides[get_product_service] = lambda: mock_service
        
        # APIリクエスト実行
        response = client.get("/api/products/999")
        
        # レスポンス検証
        assert response.status_code == 404
        data = response.json()
        assert "人物ID 999 が見つかりません" in data["detail"]
        
        # 依存性オーバーライドをクリア
        app.dependency_overrides.clear()
    
    @patch('src.api.routes.products.PersonDatabase')
    def test_get_recommended_products_no_dmm_actress_id(self, mock_db_class, client):
        """DMM女優IDが設定されていない人物のテスト"""
        # PersonDatabaseのモック設定（DMM女優IDなし）
        mock_db = Mock()
        mock_db.get_person_by_id.return_value = {
            'person_id': 1,
            'name': 'テスト女優',
            'dmm_actress_id': None
        }
        mock_db_class.return_value = mock_db
        
        # DmmProductServiceのモック設定（呼び出されないがエラーを避けるため）
        mock_service = Mock()
        app.dependency_overrides[get_product_service] = lambda: mock_service
        
        # APIリクエスト実行
        response = client.get("/api/products/1")
        
        # レスポンス検証
        assert response.status_code == 400
        data = response.json()
        assert "DMM女優IDが設定されていません" in data["detail"]
        
        # 依存性オーバーライドをクリア
        app.dependency_overrides.clear()
    
    @patch('src.api.routes.products.PersonDatabase')
    def test_get_recommended_products_limit_parameter(self, mock_db_class, client):
        """limit パラメータのテスト"""
        # モック設定
        mock_db = Mock()
        mock_db.get_person_by_id.return_value = {
            'person_id': 1,
            'name': 'テスト女優',
            'dmm_actress_id': 12345
        }
        mock_db_class.return_value = mock_db
        
        mock_service = Mock()
        mock_service.get_actress_products.return_value = []
        
        # FastAPIの依存性注入をオーバーライド
        app.dependency_overrides[get_product_service] = lambda: mock_service
        
        # 最大値（20件）を超える場合のテスト（FastAPIバリデーションにより422エラー）
        response = client.get("/api/products/1?limit=25")
        assert response.status_code == 422  # バリデーションエラー
        
        # 正常範囲内のテスト
        response = client.get("/api/products/1?limit=15")
        assert response.status_code == 200
        
        # 15件で呼び出されることを確認
        mock_service.get_actress_products.assert_called_with(
            dmm_actress_id=12345,
            limit=15
        )
        
        # 依存性オーバーライドをクリア
        app.dependency_overrides.clear()
    
    def test_get_products_by_dmm_id_success(self, client, mock_product_response):
        """DMM女優ID直接指定API の正常テスト"""
        # DmmProductServiceのモック設定
        mock_service = Mock()
        mock_service.get_actress_products.return_value = mock_product_response
        
        # FastAPIの依存性注入をオーバーライド
        app.dependency_overrides[get_product_service] = lambda: mock_service
        
        # APIリクエスト実行
        response = client.get("/api/products/by-dmm-id/12345?limit=3")
        
        # レスポンス検証
        assert response.status_code == 200
        data = response.json()
        
        assert data["dmm_actress_id"] == 12345
        assert data["total_count"] == 1
        assert len(data["products"]) == 1
        
        # モック呼び出し検証
        mock_service.get_actress_products.assert_called_once_with(
            dmm_actress_id=12345,
            limit=3
        )
        
        # 依存性オーバーライドをクリア
        app.dependency_overrides.clear()
    
    def test_get_product_api_status_success(self, client):
        """API状態確認の正常テスト"""
        # DmmProductServiceのモック設定
        mock_service = Mock()
        mock_service.check_api_status.return_value = {
            "api_configured": True,
            "api_accessible": True,
            "test_message": "API接続テスト成功"
        }
        
        # FastAPIの依存性注入をオーバーライド
        app.dependency_overrides[get_product_service] = lambda: mock_service
        
        # APIリクエスト実行
        response = client.get("/api/products/status")
        
        # レスポンス検証
        assert response.status_code == 200
        data = response.json()
        
        assert data["api_configured"] is True
        assert data["api_accessible"] is True
        assert data["test_message"] == "API接続テスト成功"
        
        # モック呼び出し検証
        mock_service.check_api_status.assert_called_once()
        
        # 依存性オーバーライドをクリア
        app.dependency_overrides.clear()
    
    def test_limit_validation(self, client):
        """limitパラメータのバリデーションテスト"""
        # モックサービスを設定（エラーを避けるため）
        mock_service = Mock()
        app.dependency_overrides[get_product_service] = lambda: mock_service
        
        # 負の値
        response = client.get("/api/products/1?limit=-1")
        assert response.status_code == 422
        
        # 0
        response = client.get("/api/products/1?limit=0")
        assert response.status_code == 422
        
        # 21（上限超過）
        response = client.get("/api/products/1?limit=21")
        assert response.status_code == 422
        
        # 依存性オーバーライドをクリア
        app.dependency_overrides.clear()
        
        # 正常範囲（1-20）はPersonDatabaseのモックが必要なので別テストで検証済み


class TestDmmProductService:
    """DmmProductService のテスト"""
    
    @patch.dict('os.environ', {
        'DMM_API_ID': 'test_api_id',
        'DMM_AFFILIATE_ID': 'test_affiliate_id'
    })
    def test_service_initialization_success(self):
        """サービス初期化の正常テスト"""
        from src.dmm.product_service import DmmProductService
        
        service = DmmProductService()
        # DmmProductServiceはDmmApiClientを内包しているのでapi_clientを通してアクセス
        assert service.api_client.api_id == 'test_api_id'
        assert service.api_client.affiliate_id == 'test_affiliate_id'
    
    @patch.dict('os.environ', {}, clear=True)
    def test_service_initialization_failure(self):
        """サービス初期化の失敗テスト（環境変数なし）"""
        from src.dmm.product_service import DmmProductService
        
        with pytest.raises(ValueError, match="DMM_API_ID と DMM_AFFILIATE_ID の環境変数が必要です"):
            DmmProductService()
    
    @patch.dict('os.environ', {
        'DMM_API_ID': 'test_api_id',
        'DMM_AFFILIATE_ID': 'test_affiliate_id'
    })
    def test_get_actress_products_success(self):
        """商品取得の正常テスト"""
        from src.dmm.product_service import DmmProductService
        from src.dmm.models import DmmApiResponse, DmmProduct, DmmImageInfo, DmmPrices
        
        # モックレスポンス作成
        image_info = DmmImageInfo(
            list_url="http://test.com/list.jpg",
            small_url="http://test.com/small.jpg",
            large_url="http://test.com/large.jpg"
        )
        prices = DmmPrices(price="1000")
        product = DmmProduct(
            content_id="test123",
            title="テスト商品",
            image_info=image_info,
            affiliate_url="http://test.com/affiliate",
            prices=prices
        )
        api_response = DmmApiResponse(
            status=200,
            result_count=1,
            total_count=1,
            products=[product]
        )
        
        # DmmApiClientをモック化
        with patch.object(DmmProductService, '__init__', lambda x: None):
            service = DmmProductService()
            mock_api_client = Mock()
            mock_api_client.search_actress_products.return_value = api_response
            service.api_client = mock_api_client
            
            # サービステスト実行
            result = service.get_actress_products(12345, limit=10)
            
            # 結果検証
            assert len(result) == 1
            product_dict = result[0]
            assert product_dict["title"] == "テスト商品"
            assert product_dict["imageURL"]["list"] == "http://test.com/list.jpg"
            assert product_dict["imageURL"]["small"] == "http://test.com/small.jpg"
            assert product_dict["imageURL"]["large"] == "http://test.com/large.jpg"
            assert product_dict["productURL"] == "http://test.com/affiliate"
            assert product_dict["prices"]["price"] == "1000"
            
            # モック呼び出し検証
            mock_api_client.search_actress_products.assert_called_once_with(
                dmm_actress_id=12345,
                limit=10
            )
    
    def test_get_actress_products_api_error(self):
        """API エラー時のテスト"""
        from src.dmm.product_service import DmmProductService
        
        # DmmApiClientをモック化（エラーレスポンス）
        with patch.object(DmmProductService, '__init__', lambda x: None):
            service = DmmProductService()
            mock_api_client = Mock()
            mock_api_client.search_actress_products.return_value = None  # エラー時はNone
            service.api_client = mock_api_client
            
            # サービステスト実行
            result = service.get_actress_products(12345)
            
            # 空のリストが返ることを確認
            assert result == []
    
    def test_get_actress_products_network_error(self):
        """ネットワークエラー時のテスト"""
        from src.dmm.product_service import DmmProductService
        
        # DmmApiClientをモック化（例外発生）
        with patch.object(DmmProductService, '__init__', lambda x: None):
            service = DmmProductService()
            mock_api_client = Mock()
            mock_api_client.search_actress_products.side_effect = Exception("Network error")
            service.api_client = mock_api_client
            
            # サービステスト実行
            result = service.get_actress_products(12345)
            
            # 空のリストが返ることを確認
            assert result == []