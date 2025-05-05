"""
画像収集モジュール

画像の収集、検証、保存を行うメインクラスを提供します。
"""

import os
from typing import Optional, Tuple
import numpy as np
import face_recognition
from PIL import Image
from io import BytesIO
from pathlib import Path
from dotenv import load_dotenv

from .search import ImageSearcher
from .download import ImageDownloader
from .storage import ImageStorage

# 環境変数の読み込み
load_dotenv()

class ImageCollector:
    """画像収集クラス"""
    
    def __init__(self):
        """画像収集クラスの初期化"""
        self.searcher = ImageSearcher()
        self.downloader = ImageDownloader()
        self.storage = ImageStorage()
        
        # 環境変数から閾値を読み込み（デフォルト値あり）
        self.similarity_threshold = float(os.getenv("SIMILARITY_THRESHOLD", "0.55"))
        self.max_faces_threshold = int(os.getenv("MAX_FACES_THRESHOLD", "1"))

    def get_base_encoding(self, base_image_path: str) -> Optional[np.ndarray]:
        """基準画像の顔エンコーディングを取得

        Args:
            base_image_path (str): 基準画像のパス

        Returns:
            Optional[np.ndarray]: 顔エンコーディング
        """
        try:
            image = face_recognition.load_image_file(base_image_path)
            encodings = face_recognition.face_encodings(image)
            if not encodings:
                print(f"警告: 基準画像から顔を検出できません: {base_image_path}")
                return None
            return encodings[0]
        except Exception as e:
            print(f"エラー: 基準画像の処理に失敗: {str(e)}")
            return None

    def validate_image(self, image_data: bytes, base_encoding: np.ndarray) -> Tuple[bool, Optional[np.ndarray]]:
        """画像の検証

        Args:
            image_data (bytes): 画像データ
            base_encoding (np.ndarray): 基準画像のエンコーディング

        Returns:
            Tuple[bool, Optional[np.ndarray]]: (検証結果, 検出された顔のエンコーディング)
        """
        try:
            # 画像を読み込み
            image = Image.open(BytesIO(image_data))
            
            # RGBA画像をRGBに変換
            if image.mode == 'RGBA':
                image = image.convert('RGB')
            
            # 画像を配列に変換
            image_array = np.array(image)
            
            # 顔の検出
            face_locations = face_recognition.face_locations(image_array)
            
            # 複数の顔が検出された場合は除外
            if len(face_locations) > self.max_faces_threshold:
                print(f"警告: 複数の顔が検出されました（{len(face_locations)}個）")
                return False, None
            
            # 顔が検出されない場合は除外
            if not face_locations:
                print("警告: 顔が検出されませんでした")
                return False, None
            
            # 顔のエンコーディングを取得
            face_encoding = face_recognition.face_encodings(image_array, face_locations)[0]
            
            # 類似度の計算
            distance = face_recognition.face_distance([base_encoding], face_encoding)[0]
            similarity = 1 - distance
            
            # 類似度が閾値を超える場合のみ有効
            if similarity >= self.similarity_threshold:
                print(f"類似度: {similarity:.2f}")
                return True, face_encoding
            
            print(f"警告: 類似度が低すぎます（{similarity:.2f}）")
            return False, None
            
        except Exception as e:
            print(f"エラー: 画像の検証に失敗: {str(e)}")
            return False, None

    def collect_images_for_person(self, person_name: str, base_image_path: str, target_count: int = 3) -> int:
        """人物の画像を収集

        Args:
            person_name (str): 人物名
            base_image_path (str): 基準画像のパス
            target_count (int): 収集する画像数

        Returns:
            int: 収集した画像数
        """
        # 基準画像のエンコーディングを取得
        base_encoding = self.get_base_encoding(base_image_path)
        if base_encoding is None:
            return 0
        
        # 画像の検索
        image_urls = self.searcher.search_images(person_name)
        collected_count = 0
        download_count = 0
        
        for url in image_urls:
            if collected_count >= target_count:
                break
                
            # 画像のダウンロード
            image_data = self.downloader.download_image(url)
            if image_data is None:
                continue
            
            download_count += 1
            validation_result = ""
            
            try:
                # 画像の検証
                is_valid, _ = self.validate_image(image_data, base_encoding)
                if is_valid:
                    collected_count += 1
                    validation_result = "valid"
                else:
                    validation_result = "invalid"
            except Exception as e:
                validation_result = "error"
                print(f"エラー: 画像の検証に失敗: {str(e)}")
            
            # すべての画像を保存
            self.storage.save_image(image_data, person_name, download_count, validation_result)
        
        print(f"\n{person_name}の結果:")
        print(f"- ダウンロードした画像数: {download_count}")
        print(f"- 有効な画像数: {collected_count}")
        return collected_count 