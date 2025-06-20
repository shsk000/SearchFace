import logging
from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from src.database.ranking_database import RankingDatabase
from src.database.search_database import SearchDatabase
from src.api.models.ranking import RankingResponse, RankingItem, RankingStatsResponse, SearchHistoryResponse
from src.utils import log_utils
from src.database.db_manager import is_sync_complete
from src.core.errors import ErrorCode
from src.core.exceptions import ServerException

router = APIRouter(tags=["ranking"])
logger = logging.getLogger(__name__)

SERVICE_UNAVAILABLE_EXCEPTION = HTTPException(
    status_code=503,
    detail="サービス準備中です。数分後に再試行してください。"
)

@router.get("/ranking", response_model=RankingResponse)
async def get_top_ranking(limit: int = 10):
    """
    検索回数に基づいた人物ランキングを取得する
    """
    if not is_sync_complete():
        raise SERVICE_UNAVAILABLE_EXCEPTION

    # Limit制約を適用（最大10）
    limit = min(limit, 10)

    try:
        ranking_db = RankingDatabase()
        ranking_data = ranking_db.get_ranking(limit=limit)

        ranking_items = [
            RankingItem(
                rank=item['rank'],
                person_id=item['person_id'],
                name=item['name'],
                win_count=item['win_count'],
                last_win_date=item['last_win_date'],
                image_path=item.get('image_path')
            ) for item in ranking_data
        ]
        
        return RankingResponse(
            ranking=ranking_items,
            total_count=len(ranking_items)
        )
    except Exception as e:
        logger.error(f"ランキング取得でエラーが発生: {str(e)}")
        raise ServerException(ErrorCode.INTERNAL_ERROR)

@router.get("/ranking/stats", response_model=RankingStatsResponse)
async def get_ranking_stats():
    """ランキング統計情報を取得"""
    ranking_db = None
    search_db = None
    try:
        ranking_db = RankingDatabase()
        search_db = SearchDatabase()

        ranking_stats = ranking_db.get_ranking_stats()
        search_stats = search_db.get_search_stats()

        # 統計情報を統合
        combined_stats = {
            **ranking_stats,
            **search_stats
        }

        return RankingStatsResponse(**combined_stats)
    except Exception as e:
        logger.error(f"統計情報取得でエラー: {str(e)}")
        raise
    finally:
        if ranking_db is not None:
            ranking_db.close()
        if search_db is not None:
            search_db.close()

@router.get("/ranking/history", response_model=SearchHistoryResponse)
async def get_search_history(limit: int = 50, person_id: int = None):
    """検索履歴を取得"""
    search_db = None
    try:
        search_db = SearchDatabase()

        if person_id:
            history_data = search_db.get_search_history(limit=limit, person_id=person_id)
        else:
            history_data = search_db.get_search_sessions(limit=limit)

        return SearchHistoryResponse(
            history=history_data,
            total_count=len(history_data)
        )
    except Exception as e:
        logger.error(f"検索履歴取得でエラー: {str(e)}")
        raise
    finally:
        if search_db is not None:
            search_db.close()
