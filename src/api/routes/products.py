"""
女優別おすすめ商品関連のAPIルーティング

女優別おすすめ商品の取得エンドポイントを提供
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import Optional, Annotated
from src.dmm.product_service import DmmProductService
from src.database.person_database import PersonDatabase
from src.utils import log_utils
import traceback

# ログ設定
logger = log_utils.get_logger(__name__)

# ルーター作成
router = APIRouter(tags=["products"])

# グローバルサービスインスタンス
_product_service: Optional[DmmProductService] = None


def get_product_service() -> DmmProductService:
    """商品取得サービスのインスタンスを取得（依存性注入）"""
    global _product_service
    
    if _product_service is None:
        try:
            _product_service = DmmProductService()
        except Exception as e:
            logger.error(f"商品取得サービス初期化エラー: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="商品取得サービスの初期化に失敗しました"
            )
    
    return _product_service


@router.get("/products/status")
async def get_product_api_status(
    product_service: DmmProductService = Depends(get_product_service)
) -> JSONResponse:
    """商品取得APIの接続状態を確認
    
    Args:
        product_service (DmmProductService): 商品取得サービス
    
    Returns:
        JSONResponse: API状態情報
    """
    try:
        logger.info("商品取得API状態確認開始")
        
        status_info = product_service.check_api_status()
        
        logger.info(f"商品取得API状態確認完了 - 接続可能: {status_info.get('api_accessible', False)}")
        
        return JSONResponse(
            status_code=200,
            content=status_info
        )
        
    except Exception as e:
        logger.error(f"商品取得API状態確認エラー: {str(e)}")
        logger.error(f"エラー詳細: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail="API状態確認中にエラーが発生しました"
        )


@router.get("/products/{person_id}")
async def get_recommended_products(
    person_id: int,
    limit: Annotated[int, Query(ge=1, le=20, description="取得件数（1-20件）")] = 10,
    product_service: DmmProductService = Depends(get_product_service)
) -> JSONResponse:
    """女優別おすすめ商品を取得
    
    Args:
        person_id (int): 人物ID
        limit (int): 取得件数（デフォルト10件、最大20件）
        product_service (DmmProductService): 商品取得サービス
    
    Returns:
        JSONResponse: 商品情報リスト
    """
    try:
        logger.info(f"女優別商品取得API開始 - 人物ID: {person_id}, 件数: {limit}")
        
        # 人物情報取得
        person_db = PersonDatabase()
        person_info = person_db.get_person_by_id(person_id)
        
        if not person_info:
            logger.warning(f"指定された人物ID({person_id})が見つかりません")
            raise HTTPException(
                status_code=404,
                detail=f"人物ID {person_id} が見つかりません"
            )
        
        # DMM女優IDチェック
        dmm_actress_id = person_info.get('dmm_actress_id')
        if not dmm_actress_id:
            logger.warning(f"人物ID({person_id})にDMM女優IDが設定されていません")
            raise HTTPException(
                status_code=400,
                detail=f"人物ID {person_id} にDMM女優IDが設定されていません"
            )
        
        # 商品取得（すでにAPIレスポンス形式で返される）
        response_data = product_service.get_actress_products(
            dmm_actress_id=dmm_actress_id,
            limit=min(limit, 20)  # 最大20件制限
        )
        
        logger.info(f"女優別商品取得API完了 - 人物ID: {person_id}, 取得件数: {len(response_data)}")
        
        return JSONResponse(
            status_code=200,
            content={
                "person_id": person_id,
                "person_name": person_info.get('name', ''),
                "dmm_actress_id": dmm_actress_id,
                "products": response_data,
                "total_count": len(response_data)
            }
        )
        
    except HTTPException:
        # HTTPExceptionはそのまま再発生
        raise
    except Exception as e:
        logger.error(f"女優別商品取得API エラー: {str(e)}")
        logger.error(f"エラー詳細: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail="内部サーバーエラーが発生しました"
        )


@router.get("/products/by-dmm-id/{dmm_actress_id}")
async def get_products_by_dmm_id(
    dmm_actress_id: int,
    limit: Annotated[int, Query(ge=1, le=20, description="取得件数（1-20件）")] = 10,
    product_service: DmmProductService = Depends(get_product_service)
) -> JSONResponse:
    """DMM女優IDで直接商品を取得（デバッグ・管理用）
    
    Args:
        dmm_actress_id (int): DMM女優ID
        limit (int): 取得件数（デフォルト10件、最大20件）
        product_service (DmmProductService): 商品取得サービス
    
    Returns:
        JSONResponse: 商品情報リスト
    """
    try:
        logger.info(f"DMM女優ID直接商品取得API開始 - 女優ID: {dmm_actress_id}, 件数: {limit}")
        
        # 商品取得（すでにAPIレスポンス形式で返される）
        response_data = product_service.get_actress_products(
            dmm_actress_id=dmm_actress_id,
            limit=min(limit, 20)  # 最大20件制限
        )
        
        logger.info(f"DMM女優ID直接商品取得API完了 - 女優ID: {dmm_actress_id}, 取得件数: {len(response_data)}")
        
        return JSONResponse(
            status_code=200,
            content={
                "dmm_actress_id": dmm_actress_id,
                "products": response_data,
                "total_count": len(response_data)
            }
        )
        
    except Exception as e:
        logger.error(f"DMM女優ID直接商品取得API エラー: {str(e)}")
        logger.error(f"エラー詳細: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail="内部サーバーエラーが発生しました"
        )