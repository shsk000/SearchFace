"""
画像保存モジュール

画像の保存とディレクトリ管理を行う機能を提供します。
"""

import hashlib
from pathlib import Path
from typing import Optional
from utils import log_utils

# ロガーの設定
logger = log_utils.get_logger(__name__)

class ImageStorage:
    """画像保存クラス"""
    
    def __init__(self):
        """画像保存クラスの初期化"""
        self.base_dir = Path("data/images/base")
        self.collected_dir = Path("data/images/collected")
        
    def generate_content_hash(self, image_data: bytes) -> str:
        """画像データからハッシュ値を生成

        Args:
            image_data (bytes): 画像データ

        Returns:
            str: ハッシュ値（16文字）
        """
        # MD5ハッシュを生成（32文字）し、最初の16文字を使用
        return hashlib.md5(image_data).hexdigest()[:16]

    def save_image(self, image_data: bytes, person_name: str, index: int, validation_result: str = "") -> bool:
        """画像の保存

        Args:
            image_data (bytes): 画像データ
            person_name (str): 人物名
            index (int): 画像のインデックス（参照用に残すが、ファイル名には使用しない）
            validation_result (str): 検証結果の説明

        Returns:
            bool: 保存の成功/失敗
        """
        try:
            # 画像データからハッシュ値を生成
            content_hash = self.generate_content_hash(image_data)
            
            # 保存先ディレクトリの決定
            if validation_result == "valid":
                # 有効な画像はcollectedディレクトリに保存
                person_dir = self.collected_dir / person_name
                image_path = person_dir / f"{person_name}_{content_hash}.jpg"
            else:
                # 無効な画像はall_imagesディレクトリに保存
                person_dir = self.collected_dir / person_name / "all_images"
                result_text = validation_result.replace(" ", "_")
                image_path = person_dir / f"{person_name}_{content_hash}_{result_text}.jpg"
            
            # ディレクトリの作成
            person_dir.mkdir(parents=True, exist_ok=True)
            
            # 既に同じファイルが存在するかチェック
            if image_path.exists():
                logger.info(f"同一内容の画像が既に存在します: {image_path}")
                return True
            
            # 画像の保存
            with open(image_path, "wb") as f:
                f.write(image_data)
            
            logger.info(f"画像を保存しました: {image_path}")
            return True
            
        except Exception as e:
            logger.error(f"画像の保存に失敗: {str(e)}")
            return False
