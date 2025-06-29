from fastapi import APIRouter, HTTPException, status, Query
from typing import Optional
from src.database.face_database import FaceDatabase
from src.database.person_database import PersonDatabase
from src.database.ranking_database import RankingDatabase
from src.api.models.response import PersonDetailResponse, PersonListResponse, PersonListItem
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
            image_path=person_data['base_image_path'] or "",
            search_count=search_count,
            dmm_list_url_digital=person_data.get('dmm_list_url_digital')
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

@router.get("/persons", response_model=PersonListResponse)
async def get_persons_list(
    limit: int = Query(20, ge=1, le=100, description="取得する件数"),
    offset: int = Query(0, ge=0, description="取得開始位置"),
    search: Optional[str] = Query(None, description="名前での検索キーワード"),
    sort_by: str = Query("name", pattern="^(name|person_id|created_at)$", description="ソート方法")
):
    """人物一覧を取得する
    
    Args:
        limit (int): 取得する件数（1-100の範囲）
        offset (int): 取得開始位置
        search (Optional[str]): 名前での検索キーワード
        sort_by (str): ソート方法 (name, person_id, created_at)
        
    Returns:
        PersonListResponse: 人物一覧情報
        
    Raises:
        HTTPException: エラーが発生した場合
    """
    person_db = None
    
    try:
        # 人物一覧取得にはFAISSインデックスは不要なので、PersonDatabaseを直接使用
        person_db = PersonDatabase()
        
        # 人物リストを取得
        persons_data = person_db.get_persons_list(
            limit=limit,
            offset=offset,
            search=search,
            sort_by=sort_by
        )
        
        # 総数を取得
        total_count = person_db.get_persons_count(search=search)
        
        # レスポンスデータを構築
        persons_items = []
        for person in persons_data:
            persons_items.append(PersonListItem(
                person_id=person['person_id'],
                name=person['name'],
                image_path=person['base_image_path'],
                dmm_actress_id=person['dmm_actress_id']
            ))
        
        # has_moreを計算
        has_more = (offset + limit) < total_count
        
        logger.info(f"人物一覧を取得: {len(persons_items)}件 (総数: {total_count})")
        
        return PersonListResponse(
            persons=persons_items,
            total_count=total_count,
            has_more=has_more
        )
        
    except Exception as e:
        logger.error(f"人物一覧の取得でエラー: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="人物一覧の取得中にエラーが発生しました"
        )
    finally:
        if person_db is not None:
            person_db.close()