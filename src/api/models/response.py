from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class SearchResult(BaseModel):
    """検索結果の1アイテムを表すモデル"""
    name: str
    similarity: float
    distance: float
    image_path: str

class SearchResponse(BaseModel):
    """検索レスポンス全体を表すモデル"""
    results: List[SearchResult]
    processing_time: float
    search_session_id: str

class SearchSessionResult(BaseModel):
    """検索セッション結果の1アイテム"""
    rank: int
    person_id: int
    name: str
    distance: float
    image_path: str

class SearchSessionResponse(BaseModel):
    """検索セッション結果レスポンス"""
    session_id: str
    search_timestamp: str
    metadata: Optional[Dict[str, Any]]
    results: List[SearchSessionResult]
