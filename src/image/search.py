"""
画像検索モジュール

Google Custom Search APIを使用して画像を検索する機能を提供します。
"""

from typing import List, Dict
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
from dotenv import load_dotenv
from utils import log_utils

# 環境変数の読み込み
load_dotenv()

# ロガーの設定
logger = log_utils.get_logger(__name__)

class ImageSearcher:
    """画像検索クラス"""
    
    def __init__(self):
        """画像検索クラスの初期化"""
        # 環境変数から設定を読み込み
        api_key = os.getenv("GOOGLE_API_KEY")
        search_engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
        
        if not api_key or not search_engine_id:
            raise ValueError(
                "環境変数が設定されていません。"
                "GOOGLE_API_KEYとGOOGLE_SEARCH_ENGINE_IDを.envファイルに設定してください。"
            )
        
        self.service = build("customsearch", "v1", developerKey=api_key)
        self.search_engine_id = search_engine_id

    def search_images(self, query: str, num: int = 10) -> List[str]:
        """画像検索の実行

        Args:
            query (str): 検索クエリ
            num (int): 取得する画像数

        Returns:
            List[str]: 画像URLのリスト
        """
        try:
            # 検索クエリの最適化
            optimized_query = f"{query} 女優"
            logger.info(f"検索クエリ: {optimized_query}")
            
            # 画像検索の実行
            result = self.service.cse().list(
                q=optimized_query,
                cx=self.search_engine_id,
                searchType="image",
                num=num,
                safe="off"
            ).execute()
            
            # 画像情報の抽出と表示
            image_urls = []
            for item in result.get("items", []):
                url = item["link"]
                mime = item.get("mime", "不明")
                file_format = item.get("fileFormat", "不明")
                logger.debug(f"検出画像: {url}")
                logger.debug(f"  MIME: {mime}")
                logger.debug(f"  形式: {file_format}")
                image_urls.append(url)
            
            logger.info(f"検索結果: {len(image_urls)}件の画像URLを取得")
            return image_urls
            
        except Exception as e:
            logger.error(f"画像検索に失敗: {str(e)}")
            return []
