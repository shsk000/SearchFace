from fastapi import APIRouter
from typing import List, Dict, Any
from src.database.ranking_database import RankingDatabase
from src.database.search_database import SearchDatabase
from src.api.models.ranking import RankingResponse, RankingItem, RankingStatsResponse, SearchHistoryResponse
from src.utils import log_utils

router = APIRouter()
logger = log_utils.get_logger(__name__)

@router.get("/ranking", response_model=RankingResponse)
async def get_ranking(limit: int = 10):
    """女優ランキングを取得"""
    # limitの上限を10件に制限
    limit = min(limit, 10)
    
    ranking_db = None
    try:
        ranking_db = RankingDatabase()
        ranking_data = ranking_db.get_ranking(limit=limit)

        return RankingResponse(
            ranking=ranking_data,
            total_count=len(ranking_data)
        )
    except Exception as e:
        logger.error(f"ランキング取得でエラー: {str(e)}")
        raise
    finally:
        if ranking_db is not None:
            ranking_db.close()

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
