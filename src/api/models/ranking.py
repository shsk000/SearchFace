from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class RankingItem(BaseModel):
    """ランキング項目"""
    rank: int
    person_id: int
    name: str
    win_count: int
    last_win_date: Optional[datetime]
    image_path: Optional[str]

class RankingResponse(BaseModel):
    """ランキングレスポンス"""
    ranking: List[RankingItem]
    total_count: int

class SearchHistoryItem(BaseModel):
    """検索履歴項目"""
    history_id: int
    search_session_id: str
    result_rank: int
    person_id: int
    name: str
    distance: float
    image_path: str
    search_timestamp: datetime
    metadata: Optional[Dict[str, Any]]

class SearchSessionItem(BaseModel):
    """検索セッション項目"""
    session_id: str
    timestamp: datetime
    result_count: int
    results: List[Dict[str, Any]]

class SearchHistoryResponse(BaseModel):
    """検索履歴レスポンス"""
    history: List[Dict[str, Any]]  # SearchHistoryItemまたはSearchSessionItem
    total_count: int

class RankingStatsResponse(BaseModel):
    """ランキング統計レスポンス"""
    total_persons: int
    total_wins: int
    top_person: Optional[Dict[str, Any]]
    total_search_sessions: int
    total_search_results: int
    first_search_date: Optional[datetime]
    latest_search_date: Optional[datetime]
