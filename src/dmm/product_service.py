"""
DMM商品取得サービス

女優別おすすめ商品を取得するためのサービスクラス
既存のDmmApiClientを活用してビジネスロジックとAPIクライアントを分離
"""

from typing import List, Dict, Any
from .dmm_api_client import DmmApiClient
from .models import DmmProduct
from src.utils import log_utils

# ログ設定
logger = log_utils.get_logger(__name__)


class DmmProductService:
    """DMM商品取得サービス"""
    
    def __init__(self):
        """初期化"""
        self.api_client = DmmApiClient()
        logger.info("DMM商品サービス初期化完了")
    
    def get_actress_products(self, dmm_actress_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """女優別おすすめ商品を取得
        
        Args:
            dmm_actress_id (int): DMM女優ID
            limit (int): 取得件数（デフォルト10件、最大20件）
            
        Returns:
            List[Dict[str, Any]]: 商品情報リスト（API レスポンス用）
        """
        try:
            logger.info(f"女優別商品取得開始 - 女優ID: {dmm_actress_id}, 件数: {limit}")
            
            # DmmApiClientを使用してAPI呼び出し
            api_response = self.api_client.search_actress_products(
                dmm_actress_id=dmm_actress_id,
                limit=min(limit, 20)  # 最大20件制限
            )
            
            if not api_response or not api_response.has_products:
                logger.info(f"商品が見つかりませんでした - 女優ID: {dmm_actress_id}")
                return []
            
            # APIレスポンス用の形式に変換
            products = []
            for product in api_response.products:
                products.append(self._convert_to_api_format(product))
            
            logger.info(f"女優別商品取得完了 - 女優ID: {dmm_actress_id}, 取得件数: {len(products)}")
            return products
            
        except Exception as e:
            logger.error(f"商品取得エラー - 女優ID: {dmm_actress_id}, エラー: {str(e)}")
            return []
    
    def _convert_to_api_format(self, product: DmmProduct) -> Dict[str, Any]:
        """DmmProductをAPIレスポンス形式に変換
        
        Args:
            product (DmmProduct): DMM商品情報
            
        Returns:
            Dict[str, Any]: APIレスポンス用の商品情報
        """
        # 価格情報をdict形式に変換
        prices_dict = {}
        if product.prices:
            if product.prices.price is not None:
                prices_dict['price'] = product.prices.price
            if product.prices.list_price is not None:
                prices_dict['list_price'] = product.prices.list_price
            if product.prices.deliveries is not None and len(product.prices.deliveries) > 0:
                deliveries_list = []
                for delivery in product.prices.deliveries:
                    deliveries_list.append({
                        'type': delivery.type,
                        'price': delivery.price
                    })
                prices_dict['deliveries'] = deliveries_list
        
        return {
            "imageURL": {
                "list": product.image_info.list_url,
                "small": product.image_info.small_url,
                "large": product.image_info.large_url
            },
            "title": product.title,
            "productURL": product.affiliate_url,
            "prices": prices_dict
        }
    
    def check_api_status(self) -> Dict[str, Any]:
        """API接続状態を確認
        
        Returns:
            Dict[str, Any]: API状態情報
        """
        try:
            logger.info("商品取得API状態確認開始")
            
            status_info = self.api_client.get_api_status()
            
            logger.info(f"商品取得API状態確認完了 - 接続可能: {status_info.get('api_accessible', False)}")
            return status_info
            
        except Exception as e:
            logger.error(f"API状態確認エラー: {str(e)}")
            return {
                "api_configured": False,
                "api_accessible": False,
                "test_message": f"状態確認エラー: {str(e)}"
            }