"""
DMM API クライアント

DMM APIを使用した商品情報取得機能を提供します。
"""

import os
import json
import requests
from typing import Optional, Dict, Any
from .models import DmmApiResponse, DmmProduct, DmmImageInfo, DmmPrices, DmmDelivery
from src.utils import log_utils

# ログ設定
logger = log_utils.get_logger(__name__)


class DmmApiClient:
    """DMM API クライアント"""
    
    # API設定
    BASE_URL = "https://api.dmm.com/affiliate/v3/ItemList"
    DEFAULT_TIMEOUT = 30
    
    def __init__(self):
        """DMM APIクライアント初期化"""
        self.api_id = os.getenv('DMM_API_ID')
        self.affiliate_id = os.getenv('DMM_AFFILIATE_ID')
        
        # 環境変数チェック
        if not self.api_id or not self.affiliate_id:
            raise ValueError("DMM_API_ID と DMM_AFFILIATE_ID の環境変数が必要です")
        
        logger.info("DMM APIクライアント初期化完了")
    
    def search_actress_products(self, dmm_actress_id: int, limit: int = 10, offset: int = 1) -> Optional[DmmApiResponse]:
        """女優IDで商品を検索
        
        Args:
            dmm_actress_id (int): DMM女優ID
            limit (int): 取得件数（最大20件）
            offset (int): 検索開始位置（1から開始）
            
        Returns:
            Optional[DmmApiResponse]: API レスポンス、エラー時はNone
        """
        params = {
            "api_id": self.api_id,
            "affiliate_id": self.affiliate_id,
            "site": "FANZA",
            "service": "digital", 
            "floor": "videoa",
            "hits": min(limit, 20),  # 最大20件制限
            "offset": max(offset, 1),  # 1以上の値
            "sort": "rank",
            "output": "json",
            "article[0]": "actress",
            "article_id[0]": str(dmm_actress_id)
        }
        
        try:
            logger.info(f"DMM API商品検索開始 - 女優ID: {dmm_actress_id}, 件数: {limit}, オフセット: {offset}")
            
            response = requests.get(
                self.BASE_URL,
                params=params,
                timeout=self.DEFAULT_TIMEOUT
            )
            response.raise_for_status()
            
            data = response.json()
            
            # レスポンス構造チェック
            result = data.get('result')
            if not result:
                logger.error("API レスポンスにresultフィールドが存在しません")
                return None
            
            # ステータスコードチェック
            status = result.get('status')
            if status != 200:
                logger.error(f"API エラー - ステータス: {status}")
                return None
            
            # 商品データ解析
            products = self._parse_products(result.get('items', []))
            
            api_response = DmmApiResponse(
                status=status,
                result_count=result.get('result_count', 0),
                total_count=result.get('total_count', 0),
                products=products
            )
            
            logger.info(f"商品検索完了 - 取得件数: {len(products)}")
            return api_response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API リクエストエラー: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON デコードエラー: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"予期しないエラー: {str(e)}")
            return None
    
    def _parse_products(self, items: list) -> list[DmmProduct]:
        """商品データを解析してDmmProductオブジェクトに変換
        
        Args:
            items (list): API レスポンスの商品リスト
            
        Returns:
            list[DmmProduct]: 解析済み商品リスト
        """
        products = []
        
        for item in items:
            try:
                # 必須フィールドチェック
                content_id = item.get('content_id')
                title = item.get('title')
                image_url_data = item.get('imageURL')
                
                if not content_id or not title or not image_url_data:
                    logger.warning(f"必須フィールドが不足した商品をスキップ: {content_id}")
                    continue
                
                # 画像URL情報を解析
                image_info = DmmImageInfo(
                    list_url=image_url_data.get('list', ''),
                    small_url=image_url_data.get('small', ''),
                    large_url=image_url_data.get('large', '')
                )
                
                # 大サイズ画像URLが存在しない場合はスキップ
                if not image_info.large_url:
                    logger.warning(f"大サイズ画像URLが存在しない商品をスキップ: {content_id}")
                    continue
                
                # アフィリエイトURL取得
                affiliate_url = item.get('affiliateURL', '')
                
                # 価格情報取得
                prices = self._extract_prices(item)
                
                # 出演女優数をチェック
                iteminfo = item.get('iteminfo', {})
                actress_list = iteminfo.get('actress', [])
                actress_count = len(actress_list) if actress_list else 1
                
                product = DmmProduct(
                    content_id=content_id,
                    title=title,
                    image_info=image_info,
                    actress_count=actress_count,
                    affiliate_url=affiliate_url,
                    prices=prices
                )
                
                products.append(product)
                
            except Exception as e:
                logger.warning(f"商品データ解析エラー: {str(e)}")
                continue
        
        return products
    
    def _extract_prices(self, item: Dict[str, Any]) -> DmmPrices:
        """商品の価格情報を抽出（API仕様準拠）
        
        Args:
            item (Dict[str, Any]): 商品データ
            
        Returns:
            DmmPrices: 価格情報（dataclass形式）
        """
        try:
            # 価格情報の取得
            prices_data = item.get('prices', {})
            
            if not prices_data:
                # 価格情報が存在しない場合のデフォルト
                return DmmPrices(price='価格未設定')
            
            # price: 金額 (300～)
            price = prices_data.get('price')
            if price is not None:
                price = str(price)
            
            # list_price: 定価
            list_price = prices_data.get('list_price')
            if list_price is not None:
                list_price = str(list_price)
            
            # deliveries: 配信リスト
            deliveries = []
            deliveries_list = prices_data.get('deliveries', [])
            if deliveries_list and isinstance(deliveries_list, list):
                for delivery in deliveries_list:
                    if isinstance(delivery, dict):
                        delivery_type = delivery.get('type')
                        delivery_price = delivery.get('price')
                        
                        # type と price の両方が存在する場合のみ追加
                        if delivery_type is not None and delivery_price is not None:
                            deliveries.append(DmmDelivery(
                                type=str(delivery_type),
                                price=str(delivery_price)
                            ))
            
            return DmmPrices(
                price=price,
                list_price=list_price,
                deliveries=deliveries if deliveries else None
            )
                
        except Exception as e:
            logger.warning(f"価格情報抽出エラー: {str(e)}")
            return DmmPrices(price='価格未設定')
    
    def get_api_status(self) -> Dict[str, Any]:
        """API接続状態を確認
        
        Returns:
            Dict[str, Any]: API状態情報
        """
        status_info = {
            "api_configured": bool(self.api_id and self.affiliate_id),
            "api_id_set": bool(self.api_id),
            "affiliate_id_set": bool(self.affiliate_id)
        }
        
        if status_info["api_configured"]:
            # 簡単なテストリクエスト（存在しない女優IDでテスト）
            try:
                response = requests.get(
                    self.BASE_URL,
                    params={
                        "api_id": self.api_id,
                        "affiliate_id": self.affiliate_id,
                        "site": "FANZA",
                        "service": "digital",
                        "floor": "videoa",
                        "hits": 1,
                        "output": "json",
                        "article[0]": "actress",
                        "article_id[0]": "999999999"  # 存在しないID
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('result', {}).get('status') == 200:
                        status_info["api_accessible"] = True
                        status_info["test_message"] = "API接続テスト成功"
                    else:
                        status_info["api_accessible"] = False
                        status_info["test_message"] = f"API エラー: {data.get('result', {}).get('status')}"
                else:
                    status_info["api_accessible"] = False
                    status_info["test_message"] = f"HTTP エラー: {response.status_code}"
                    
            except Exception as e:
                status_info["api_accessible"] = False
                status_info["test_message"] = f"接続テストエラー: {str(e)}"
        else:
            status_info["api_accessible"] = False
            status_info["test_message"] = "API認証情報が未設定"
        
        return status_info