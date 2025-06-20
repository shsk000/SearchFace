import os
import time
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List, Dict, Any
import io
import numpy as np
from PIL import Image
from src.core.errors import ErrorCode
from src.core.exceptions import ImageValidationException, ServerException
import logging

from src.database.face_database import FaceDatabase
from src.face import face_utils
from src.utils.similarity import calculate_similarity
from src.api.models.response import SearchResult, SearchResponse, SearchSessionResponse, SearchSessionResult

# 新しいデータベースクラスとマネージャーをインポート
from src.database.search_database import SearchDatabase
from src.database.ranking_database import RankingDatabase
from src.database.db_manager import get_search_db_connection, get_ranking_db_connection, is_sync_complete

router = APIRouter(tags=["search"])
logger = logging.getLogger(__name__)

SERVICE_UNAVAILABLE_EXCEPTION = HTTPException(
    status_code=503,
    detail="サービス準備中です。数分後に再試行してください。"
)

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
    if not is_sync_complete():
        raise SERVICE_UNAVAILABLE_EXCEPTION

    start_time = time.time()

    # 画像の検証
    if not image.content_type.startswith('image/'):
        raise ImageValidationException(ErrorCode.INVALID_IMAGE_FORMAT)

    # 画像サイズの検証（500KB以下）
    if image.size > 500 * 1024:  # 500KB
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
        search_start = time.time()
        results = db.search_similar_faces(face_encoding, top_k=top_k)
        search_time = time.time() - search_start
        logger.debug(f"類似顔検索時間: {search_time:.4f}秒")

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
        session_id = None

        # 検索結果がある場合、ランキングデータベースに記録（person_idベース）
        if search_results and results:
            record_start = time.time()

            # グローバルな接続を取得
            search_conn = get_search_db_connection()
            ranking_conn = get_ranking_db_connection()

            if not search_conn or not ranking_conn:
                logger.error("データベース接続が利用できません。記録をスキップします。")
            else:
                try:
                    # データベースインスタンスを生成
                    search_db = SearchDatabase(search_conn)
                    ranking_db = RankingDatabase(ranking_conn)

                    # 検索履歴を記録
                    record_search_start = time.time()
                    session_id = search_db.record_search_results(
                        search_results=results,
                        metadata={
                            'filename': image.filename,
                            'file_size': image.size,
                            'processing_time': processing_time
                        }
                    )
                    record_search_time = time.time() - record_search_start
                    logger.debug(f"検索履歴記録時間: {record_search_time:.4f}秒")

                    # 1位結果をランキングに反映
                    ranking_start = time.time()
                    if session_id:
                        winner = results[0]
                        ranking_db.update_ranking(person_id=winner['person_id'])
                        ranking_time = time.time() - ranking_start
                        logger.debug(f"ランキング更新時間: {ranking_time:.4f}秒")
                        logger.info(f"検索結果記録完了: セッション={session_id}, 1位={winner['name']}")
                    else:
                        logger.warning("セッションIDの取得に失敗したため、ランキング更新をスキップします。")

                except Exception as db_error:
                    logger.error(f"検索結果の記録に失敗（検索は成功）: {str(db_error)}")
                finally:
                    total_record_time = time.time() - record_start
                    logger.debug(f"検索結果記録処理総時間: {total_record_time:.4f}秒")

        logger.debug(f"results: {search_results}")

        # レスポンス生成
        response_start = time.time()
        response = SearchResponse(
            results=search_results,
            processing_time=processing_time,
            search_session_id=session_id or ""
        )
        response_time = time.time() - response_start
        logger.debug(f"レスポンス生成時間: {response_time:.4f}秒")

        return response

    except ImageValidationException:
        raise
    except Exception as e:
        logger.error(f"検索処理でエラーが発生: {str(e)}")
        raise ServerException(ErrorCode.INTERNAL_ERROR)

@router.get("/search/{session_id}", response_model=SearchSessionResponse)
async def get_search_session_results(session_id: str):
    """
    検索セッションIDから検索結果を取得する

    Args:
        session_id: 検索セッションID

    Returns:
        SearchSessionResponse: セッションの検索結果

    Raises:
        ServerException: セッションが見つからない場合やサーバーエラーが発生した場合
    """
    if not is_sync_complete():
        raise SERVICE_UNAVAILABLE_EXCEPTION

    try:
        search_conn = get_search_db_connection()
        if not search_conn:
            raise HTTPException(status_code=503, detail="データベースサービスが利用できません。")

        search_db = SearchDatabase(search_conn)
        session_data = search_db.get_search_session_results(session_id)

        if not session_data:
            raise ServerException(ErrorCode.SESSION_NOT_FOUND)

        # レスポンス形式に変換
        session_results = []
        for result in session_data['results']:
            # 類似度の計算（exponentialがデフォルト）
            similarity = calculate_similarity({'distance': result['distance']}, method='exponential')

            session_results.append(
                SearchSessionResult(
                    rank=result['rank'],
                    person_id=result['person_id'],
                    name=result['name'],
                    similarity=float(similarity),
                    distance=result['distance'],
                    image_path=result['image_path']
                )
            )

        return SearchSessionResponse(
            session_id=session_data['session_id'],
            search_timestamp=session_data['search_timestamp'],
            metadata=session_data['metadata'],
            results=session_results
        )

    except ServerException:
        raise
    except Exception as e:
        logger.error(f"セッション結果取得でエラーが発生: {str(e)}")
        raise ServerException(ErrorCode.INTERNAL_ERROR)
