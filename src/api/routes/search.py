import time
from fastapi import APIRouter, UploadFile, File
from typing import List, Dict, Any
import io
import numpy as np
from PIL import Image
from src.core.errors import ErrorCode
from src.core.exceptions import ImageValidationException, ServerException
import logging

from database.face_database import FaceDatabase
from face import face_utils
from utils.similarity import calculate_similarity
from api.models.response import SearchResult, SearchResponse

router = APIRouter(prefix="/api", tags=["search"])
logger = logging.getLogger(__name__)

@router.post("/search", response_model=SearchResponse)
async def search_face(
    image: UploadFile = File(...),
    top_k: int = 5
):
    """
    アップロードされた画像から顔を検出し、類似する顔を検索する

    Args:
        image: アップロードされた画像ファイル（対応形式: JPEG, PNG, BMP）
        top_k: 返却する結果の数（デフォルト: 5）

    Returns:
        SearchResponse: 検索結果と処理時間を含むレスポンス

    Raises:
        ImageValidationException: 画像の検証に失敗した場合
        ServerException: サーバーエラーが発生した場合
    """
    start_time = time.time()

    # 画像の検証
    if not image.content_type.startswith('image/'):
        raise ImageValidationException(ErrorCode.INVALID_IMAGE_FORMAT)

    # 画像サイズの検証（5MB以下）
    if image.size > 5 * 1024 * 1024:  # 5MB
        raise ImageValidationException(ErrorCode.IMAGE_TOO_LARGE)

    try:
        # 画像の読み込みと検証
        contents = await image.read()
        img = Image.open(io.BytesIO(contents))
        # RGBA画像をRGBに変換
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        img_array = np.array(img)
    except Exception as e:
        logger.error(f"画像の読み込みに失敗: {str(e)}")
        raise ImageValidationException(ErrorCode.IMAGE_CORRUPTED)

    # 顔の検出
    # 複数顔検出時はImageValidationException(ErrorCode.MULTIPLE_FACES)がraiseされる
    face_encoding = face_utils.get_face_encoding_from_array(img_array)
    if face_encoding is None:
        raise ImageValidationException(ErrorCode.NO_FACE_DETECTED)

    # 類似顔の検索
    db = FaceDatabase()
    try:
        results = db.search_similar_faces(face_encoding, top_k=top_k)

        if not results:
            raise ImageValidationException(ErrorCode.NO_FACE_DETECTED)

        # 結果の変換
        search_results = []
        for result in results:
            # 類似度の計算（exponentialがデフォルト）
            similarity = calculate_similarity(result, method='exponential')

            search_results.append(
                SearchResult(
                    name=result["name"],
                    similarity=float(similarity),
                    distance=float(result["distance"]),
                    image_path=result["image_path"]
                )
            )

        processing_time = time.time() - start_time

        logger.debug(f"results: {search_results}")

        return SearchResponse(
            results=search_results,
            processing_time=processing_time
        )

    except ImageValidationException:
        raise
    except Exception as e:
        logger.error(f"検索処理でエラーが発生: {str(e)}")
        raise ServerException(ErrorCode.INTERNAL_ERROR)
    finally:
        db.close()
