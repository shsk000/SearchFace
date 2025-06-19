"""
DMM用画像ダウンローダー

DMM APIから取得した画像URLの画像をダウンロードする機能を提供します。
"""

from typing import Optional
import requests
from PIL import Image
from io import BytesIO
import time
import urllib3
from src.utils import log_utils

# SSL警告を無効化
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ログ設定
logger = log_utils.get_logger(__name__)


class DmmImageDownloader:
    """DMM用画像ダウンローダー"""
    
    def __init__(self):
        """初期化"""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
            'Referer': 'https://www.dmm.co.jp/'
        }
        self.timeout = 30
        self.max_retries = 3
    
    def download_image(self, url: str) -> Optional[bytes]:
        """画像をダウンロード
        
        Args:
            url (str): 画像URL
            
        Returns:
            Optional[bytes]: 画像データ、失敗時はNone
        """
        for attempt in range(self.max_retries):
            try:
                # リクエスト実行
                response = requests.get(
                    url,
                    headers=self.headers,
                    timeout=self.timeout,
                    verify=False
                )
                response.raise_for_status()
                
                # Content-Type確認
                content_type = response.headers.get('content-type', '').lower()
                if not content_type.startswith('image/'):
                    logger.warning(f"画像以外のコンテンツタイプ: {content_type}")
                    return None
                
                # 画像データ検証
                try:
                    Image.open(BytesIO(response.content))
                except Exception as e:
                    logger.warning(f"無効な画像データ: {str(e)}")
                    return None
                
                logger.debug(f"画像ダウンロード成功: {len(response.content)} bytes")
                return response.content
                
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries - 1:
                    logger.warning(f"リトライ中... ({attempt + 1}/{self.max_retries}): {str(e)}")
                    time.sleep(1)
                    continue
                logger.error(f"画像ダウンロード失敗: {str(e)}")
                return None
            except Exception as e:
                logger.error(f"予期しないエラー: {str(e)}")
                return None
        
        return None