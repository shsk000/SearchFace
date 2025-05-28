from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class SearchResult(BaseModel):
    """検索結果の1アイテムを表すモデル"""
    name: str
    similarity: float
    image_path: str
    metadata: Optional[Dict[str, Any]] = None

class SearchResponse(BaseModel):
    """検索レスポンス全体を表すモデル"""
    results: List[SearchResult]
    processing_time: float
