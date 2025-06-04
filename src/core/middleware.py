"""
エラーハンドリングミドルウェア

このモジュールは以下の機能を提供します：
1. アプリケーション全体のエラーハンドリング
2. エラーレスポンスの標準化
3. エラーログの記録
"""

import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from src.core.errors import ErrorCode
from src.core.exceptions import BaseException

logger = logging.getLogger(__name__)

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """エラーハンドリングを行うミドルウェア"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """リクエストを処理し、エラーをハンドリングする
        
        Args:
            request (Request): FastAPIのリクエストオブジェクト
            call_next (Callable): 次のミドルウェアまたはルートハンドラを呼び出す関数
            
        Returns:
            Response: エラーレスポンスまたは正常なレスポンス
        """
        try:
            return await call_next(request)
            
        except BaseException as e:
            # カスタム例外の処理
            logger.error(f"エラーが発生しました: {str(e)}")
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": {
                        "code": e.code,
                        "message": e.message
                    }
                }
            )
            
        except Exception as e:
            # 予期せぬエラーの処理
            logger.error(f"予期せぬエラーが発生しました: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": ErrorCode.SERVER_ERROR,
                        "message": "サーバーエラーが発生しました"
                    }
                }
            )

async def error_handler_middleware(request: Request, call_next: Callable) -> Response:
    """エラーハンドリングミドルウェア
    
    Args:
        request (Request): FastAPIのリクエストオブジェクト
        call_next (Callable): 次のミドルウェアまたはルートハンドラを呼び出す関数
        
    Returns:
        Response: エラーレスポンスまたは正常なレスポンス
    """
    try:
        return await call_next(request)
        
    except BaseException as e:
        # カスタム例外の処理
        logger.error(f"エラーが発生しました: {str(e)}")
        return JSONResponse(
            status_code=e.status_code,
            content={
                "error": {
                    "code": e.code,
                    "message": e.message
                }
            }
        )
        
    except Exception as e:
        # 予期せぬエラーの処理
        logger.error(f"予期せぬエラーが発生しました: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": ErrorCode.SERVER_ERROR,
                    "message": "サーバーエラーが発生しました"
                }
            }
        ) 