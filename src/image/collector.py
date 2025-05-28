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
from utils import log_utils
from face.face_utils import get_face_encoding, detect_faces
from utils.similarity import sigmoid_similarity

# 環境変数の読み込み
load_dotenv()

# ロガーの設定
logger = log_utils.get_logger(__name__)

class ImageCollector:
    """画像収集クラス"""
    
    def __init__(self):
        """画像収集クラスの初期化"""
        self.searcher = ImageSearcher()
        self.downloader = ImageDownloader()
        self.storage = ImageStorage()

        self.similarity_threshold = float("0.55");
        self.max_faces_threshold = int(os.getenv("MAX_FACES_THRESHOLD", "1"))
        logger.info(f"類似度閾値: {self.similarity_threshold}, 最大顔検出数: {self.max_faces_threshold}")

    def get_base_encoding(self, base_image_path: str) -> Optional[np.ndarray]:
        """基準画像の顔エンコーディングを取得

        Args:
            base_image_path (str): 基準画像のパス

        Returns:
            Optional[np.ndarray]: 顔エンコーディング
        """
        # face_utils.pyのget_face_encoding関数を使用
        encoding = get_face_encoding(base_image_path)
        if encoding is None:
            logger.warning(f"基準画像から顔を検出できません: {base_image_path}")
        return encoding

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
            
            # face_utils.pyのdetect_faces関数を使用して顔検出とエンコーディング取得
            face_encodings, face_locations = detect_faces(image_array)
            
            # 複数の顔が検出された場合は除外
            if len(face_locations) > self.max_faces_threshold:
                logger.warning(f"複数の顔が検出されました（{len(face_locations)}個）")
                return False, None
            
            # 顔が検出されない場合は除外
            if not face_locations:
                logger.warning("顔が検出されませんでした")
                return False, None
            
            # 顔のエンコーディングを取得
            face_encoding = face_encodings[0]
            
            # 類似度の計算
            distance = face_recognition.face_distance([base_encoding], face_encoding)[0]
            # similarity.pyのexponential_similarity関数を使用
            similarity = sigmoid_similarity(distance)
            
            logger.debug(f"距離={distance:.2f}, 類似度={similarity:.2f}, 閾値={self.similarity_threshold:.2f}")
            
            # 類似度の判定
            if similarity >= self.similarity_threshold:
                logger.info(f"類似度: {similarity:.2f}（閾値: {self.similarity_threshold:.2f}）")
                return True, face_encoding
            
            logger.warning(f"類似度が閾値を下回っています（{similarity:.2f} < {self.similarity_threshold:.2f}）")
            return False, None
            
        except Exception as e:
            logger.error(f"画像の検証に失敗: {str(e)}")
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
                logger.error(f"画像の検証に失敗: {str(e)}")
            
            # すべての画像を保存
            self.storage.save_image(image_data, person_name, download_count, validation_result)
        
        logger.info(f"\n{person_name}の結果:")
        logger.info(f"- ダウンロードした画像数: {download_count}")
        logger.info(f"- 有効な画像数: {collected_count}")
        return collected_count
