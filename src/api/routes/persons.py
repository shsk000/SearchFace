from fastapi import APIRouter, HTTPException, status
from src.database.face_database import FaceDatabase
from src.database.ranking_database import RankingDatabase
from src.api.models.response import PersonDetailResponse
from src.utils import log_utils

router = APIRouter()
logger = log_utils.get_logger(__name__)

@router.get("/persons/{person_id}", response_model=PersonDetailResponse)
async def get_person_detail(person_id: int):
    """人物詳細情報を取得する
    
    Args:
        person_id (int): 人物ID
        
    Returns:
        PersonDetailResponse: 人物詳細情報
        
    Raises:
        HTTPException: 人物が見つからない場合、またはエラーが発生した場合
    """
    face_db = None
    ranking_db = None
    
    try:
        # ローカルSQLiteから基本情報を取得
        face_db = FaceDatabase()
        person_data = face_db.get_person_detail(person_id)
        
        if not person_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"人物ID {person_id} が見つかりません"
            )
        
        # Tursoから検索回数を取得
        ranking_db = RankingDatabase()
        search_count = ranking_db.get_person_search_count(person_id)
        
        return PersonDetailResponse(
            person_id=person_data['person_id'],
            name=person_data['name'],
            image_path=person_data['image_path'] or "",
            search_count=search_count
        )
        
    except HTTPException:
        # HTTPException は再発生させる
        raise
    except Exception as e:
        logger.error(f"人物詳細情報の取得でエラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="人物詳細情報の取得中にエラーが発生しました"
        )
    finally:
        if face_db is not None:
            face_db.close()
        if ranking_db is not None:
            ranking_db.close()