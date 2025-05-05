"""
画像保存モジュール

画像の保存とディレクトリ管理を行う機能を提供します。
"""

from pathlib import Path
from typing import Optional

class ImageStorage:
    """画像保存クラス"""
    
    def __init__(self):
        """画像保存クラスの初期化"""
        self.base_dir = Path("data/images/base")
        self.collected_dir = Path("data/images/collected")

    def save_image(self, image_data: bytes, person_name: str, index: int, validation_result: str = "") -> bool:
        """画像の保存

        Args:
            image_data (bytes): 画像データ
            person_name (str): 人物名
            index (int): 画像のインデックス
            validation_result (str): 検証結果の説明

        Returns:
            bool: 保存の成功/失敗
        """
        try:
            # 保存先ディレクトリの決定
            if validation_result == "valid":
                # 有効な画像はcollectedディレクトリに保存
                person_dir = self.collected_dir / person_name
                image_path = person_dir / f"{person_name}_{index}.jpg"
            else:
                # 無効な画像はall_imagesディレクトリに保存
                person_dir = self.collected_dir / person_name / "all_images"
                result_text = validation_result.replace(" ", "_")
                image_path = person_dir / f"{person_name}_{index}_{result_text}.jpg"
            
            # ディレクトリの作成
            person_dir.mkdir(parents=True, exist_ok=True)
            
            # 画像の保存
            with open(image_path, "wb") as f:
                f.write(image_data)
            
            print(f"画像を保存しました: {image_path}")
            return True
            
        except Exception as e:
            print(f"エラー: 画像の保存に失敗: {str(e)}")
            return False 