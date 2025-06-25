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
    similarity: float
    distance: float
    image_path: str

class SearchSessionResponse(BaseModel):
    """検索セッション結果レスポンス"""
    session_id: str
    search_timestamp: str
    metadata: Optional[Dict[str, Any]]
    results: List[SearchSessionResult]

class PersonDetailResponse(BaseModel):
    """人物詳細情報レスポンス"""
    person_id: int
    name: str
    image_path: str
    search_count: int

class PersonListItem(BaseModel):
    """人物リストアイテム"""
    person_id: int
    name: str
    image_path: Optional[str]
    dmm_actress_id: Optional[int]

class PersonListResponse(BaseModel):
    """人物リストレスポンス"""
    persons: List[PersonListItem]
    total_count: int
    has_more: bool
