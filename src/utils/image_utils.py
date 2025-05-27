import hashlib
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)

def calculate_image_hash(image_path: str) -> str:
    """
    画像のハッシュ値を計算する
    
    Args:
        image_path: 画像ファイルのパス
        
    Returns:
        str: 画像のハッシュ値。エラー時は空文字列を返す
    """
    try:
        with Image.open(image_path) as img:
            # 画像をバイト列に変換
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format=img.format)
            img_byte_arr = img_byte_arr.getvalue()
            
            # SHA-256ハッシュを計算
            return hashlib.sha256(img_byte_arr).hexdigest()
    except Exception as e:
        logger.error(f"画像ハッシュの計算に失敗しました: {str(e)}")
        return "" 