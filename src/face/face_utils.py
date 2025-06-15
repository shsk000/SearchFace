import face_recognition
import numpy as np
from typing import List, Tuple, Optional
import requests
from PIL import Image
from io import BytesIO
from src.utils import log_utils
from src.core.exceptions import ImageValidationException
from src.core.errors import ErrorCode

# ロガーの設定
logger = log_utils.get_logger(__name__)

def load_image(image_path: str) -> Optional[np.ndarray]:
    """
    画像を読み込む（ローカルファイルまたはURL）

    Args:
        image_path (str): 画像ファイルのパスまたはURL

    Returns:
        Optional[np.ndarray]: 読み込んだ画像データ。失敗時はNone
    """
    try:
        logger.debug(f"画像を読み込んでいます: {image_path}")
        
        # URLの場合はload_image_from_urlを使用
        if image_path.startswith(('http://', 'https://')):
            return load_image_from_url(image_path)
        else:
            # ローカルファイルの場合は従来通り
            return face_recognition.load_image_file(image_path)
            
    except Exception as e:
        logger.error(f"画像の読み込みに失敗しました: {image_path}")
        logger.error(f"エラー: {str(e)}")
        return None

def load_image_from_url(url: str) -> Optional[np.ndarray]:
    """
    URLから画像を読み込む

    Args:
        url (str): 画像のURL

    Returns:
        Optional[np.ndarray]: 読み込んだ画像データ。失敗時はNone
    """
    try:
        logger.debug(f"URLから画像を読み込んでいます: {url}")
        response = requests.get(url, timeout=30, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        response.raise_for_status()
        
        # PILで画像を開いてnumpy配列に変換
        image = Image.open(BytesIO(response.content))
        # RGBに変換（face_recognitionはRGB形式を期待）
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        return np.array(image)
    except Exception as e:
        logger.error(f"URLからの画像読み込みに失敗しました: {url}")
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
    # 顔の位置を検出（HOGモデル優先、失敗時はCNNモデル）
    logger.debug("顔の位置を検出しています...")
    
    # まずHOGモデルで試行（高速）
    face_locations = face_recognition.face_locations(image, model='hog')
    logger.debug(f"HOGモデル検出数: {len(face_locations)}")
    
    # HOGで検出できない場合はCNNモデルを試行（精度重視）
    if len(face_locations) == 0:
        logger.debug("HOGモデルで検出できませんでした。CNNモデルを試行します...")
        try:
            face_locations = face_recognition.face_locations(image, model='cnn')
            logger.debug(f"CNNモデル検出数: {len(face_locations)}")
        except Exception as e:
            logger.warning(f"CNNモデルでの検出に失敗: {str(e)}")
            face_locations = []
    
    logger.debug(f"最終的な検出された顔の数: {len(face_locations)}")

    # 顔のエンコーディングを取得
    logger.debug("顔のエンコーディングを取得しています...")
    face_encodings = face_recognition.face_encodings(image, face_locations)
    logger.debug(f"取得されたエンコーディングの数: {len(face_encodings)}")

    return face_encodings, face_locations

def get_face_encoding(image_path: str) -> Optional[np.ndarray]:
    """
    画像から顔のエンコーディングを取得する

    Args:
        image_path (str): 画像ファイルのパスまたはURL

    Returns:
        Optional[np.ndarray]: 顔のエンコーディング。失敗時はNone
    """
    # URLの場合はURLから読み込み、そうでなければファイルから読み込み
    if image_path.startswith(('http://', 'https://')):
        image = load_image_from_url(image_path)
    else:
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
        logger.warning(f"複数の顔が検出されました: {image_path}")
        raise ImageValidationException(ErrorCode.MULTIPLE_FACES)

    return face_encodings[0]

def get_face_encoding_from_array(image_array: np.ndarray) -> Optional[np.ndarray]:
    """
    画像配列から顔のエンコーディングを取得する

    Args:
        image_array (np.ndarray): 画像データの配列

    Returns:
        Optional[np.ndarray]: 顔のエンコーディング。失敗時はNone
    """
    # 顔を検出
    face_encodings, _ = detect_faces(image_array)

    # 顔が検出されなかった場合
    if not face_encodings:
        logger.warning("顔が検出されませんでした")
        return None

    # 複数の顔が検出された場合
    if len(face_encodings) > 1:
        logger.warning("複数の顔が検出されました")
        from src.core.exceptions import ImageValidationException
        from src.core.errors import ErrorCode
        raise ImageValidationException(ErrorCode.MULTIPLE_FACES)

    return face_encodings[0]
