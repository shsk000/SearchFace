import face_recognition
import numpy as np
from typing import List, Tuple, Optional
from utils import log_utils

# ロガーの設定
logger = log_utils.get_logger(__name__)

def load_image(image_path: str) -> Optional[np.ndarray]:
    """
    画像を読み込む
    
    Args:
        image_path (str): 画像ファイルのパス
        
    Returns:
        Optional[np.ndarray]: 読み込んだ画像データ。失敗時はNone
    """
    try:
        logger.debug(f"画像を読み込んでいます: {image_path}")
        return face_recognition.load_image_file(image_path)
    except Exception as e:
        logger.error(f"画像の読み込みに失敗しました: {image_path}")
        logger.error(f"エラー: {str(e)}")
        return None

def detect_faces(image: np.ndarray) -> Tuple[List[np.ndarray], List[Tuple[int, int, int, int]]]:
    """
    画像から顔を検出し、エンコーディングを取得する
    
    Args:
        image (np.ndarray): 画像データ
        
    Returns:
        Tuple[List[np.ndarray], List[Tuple[int, int, int, int]]]: 
            - 顔エンコーディングのリスト
            - 顔の位置（top, right, bottom, left）のリスト
    """
    # 顔の位置を検出
    logger.debug("顔の位置を検出しています...")
    face_locations = face_recognition.face_locations(image)
    logger.debug(f"検出された顔の数: {len(face_locations)}")
    
    # 顔のエンコーディングを取得
    logger.debug("顔のエンコーディングを取得しています...")
    face_encodings = face_recognition.face_encodings(image, face_locations)
    logger.debug(f"取得されたエンコーディングの数: {len(face_encodings)}")
    
    return face_encodings, face_locations

def get_face_encoding(image_path: str) -> Optional[np.ndarray]:
    """
    画像から顔のエンコーディングを取得する
    
    Args:
        image_path (str): 画像ファイルのパス
        
    Returns:
        Optional[np.ndarray]: 顔のエンコーディング。失敗時はNone
    """
    # 画像を読み込む
    image = load_image(image_path)
    if image is None:
        return None
    
    # 顔を検出
    face_encodings, _ = detect_faces(image)
    
    # 顔が検出されなかった場合
    if not face_encodings:
        logger.warning(f"顔が検出されませんでした: {image_path}")
        return None
    
    # 複数の顔が検出された場合
    if len(face_encodings) > 1:
        logger.warning(f"複数の顔が検出されました。最初の顔を使用します: {image_path}")
    
    return face_encodings[0]
