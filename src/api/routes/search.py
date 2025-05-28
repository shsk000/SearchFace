import time
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
import io
import numpy as np
from PIL import Image

from database.face_database import FaceDatabase
from face import face_utils
from utils.similarity import calculate_similarity
from api.models.response import SearchResult, SearchResponse

router = APIRouter(prefix="/api", tags=["search"])

@router.post("/search", response_model=SearchResponse)
async def search_faces(image: UploadFile = File(...)):
    """
    アップロードされた画像から顔を検出し、類似する顔を検索する
    
    Args:
        image: アップロードされた画像ファイル（対応形式: JPEG, PNG, BMP）
        
    Returns:
        SearchResponse: 検索結果と処理時間を含むレスポンス
        
    Raises:
        HTTPException: 画像の読み込みや顔の検出に失敗した場合
    """
    start_time = time.time()
    
    # 画像の読み込みと検証
    try:
        contents = await image.read()
        img = Image.open(io.BytesIO(contents))
        # RGBA画像をRGBに変換
        if img.mode == 'RGBA':
            img = img.convert('RGB')
        img_array = np.array(img)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"無効な画像ファイル: {str(e)}")
    
    # 顔の検出
    face_encoding = face_utils.get_face_encoding_from_array(img_array)
    if face_encoding is None:
        raise HTTPException(status_code=400, detail="画像から顔を検出できませんでした")
    
    # 類似顔の検索
    db = FaceDatabase()
    try:
        results = db.search_similar_faces(face_encoding, top_k=3)
        
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
        
        return SearchResponse(
            results=search_results,
            processing_time=processing_time
        )
    
    finally:
        db.close()
