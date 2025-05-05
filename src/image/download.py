"""
画像ダウンロードモジュール

画像のダウンロードと検証を行う機能を提供します。
"""

from typing import Optional
import requests
from PIL import Image
from io import BytesIO
import time
import urllib3

# SSL警告を無効化
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ImageDownloader:
    """画像ダウンロードクラス"""
    
    def __init__(self):
        """画像ダウンロードクラスの初期化"""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
            'Referer': 'https://www.google.com/'
        }

    def download_image(self, url: str, max_retries: int = 3) -> Optional[bytes]:
        """画像のダウンロード

        Args:
            url (str): 画像URL
            max_retries (int): 最大リトライ回数

        Returns:
            Optional[bytes]: 画像データ
        """
        for attempt in range(max_retries):
            try:
                # URLがTikTokの場合はスキップ
                if "tiktok.com" in url:
                    print(f"警告: TikTok URLはスキップします: {url}")
                    return None
                
                # リクエストの実行
                response = requests.get(
                    url,
                    headers=self.headers,
                    timeout=30,
                    verify=False
                )
                response.raise_for_status()
                
                # Content-Typeの確認
                content_type = response.headers.get('content-type', '').lower()
                if not content_type.startswith('image/'):
                    print(f"警告: 画像以外のコンテンツタイプです: {content_type}")
                    return None
                
                # 画像データの検証
                try:
                    Image.open(BytesIO(response.content))
                except Exception as e:
                    print(f"警告: 無効な画像データです: {str(e)}")
                    return None
                
                return response.content
                
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    print(f"警告: リトライ中... ({attempt + 1}/{max_retries}): {str(e)}")
                    time.sleep(1)  # リトライ前に1秒待機
                    continue
                print(f"エラー: 画像のダウンロードに失敗: {str(e)}")
                return None
            except Exception as e:
                print(f"エラー: 予期せぬエラーが発生: {str(e)}")
                return None
        
        return None 