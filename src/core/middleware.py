from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from .errors import ErrorCode
from .exceptions import ImageValidationException, ServerException
import logging

logger = logging.getLogger(__name__)

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            return await call_next(request)
        except ImageValidationException as e:
            logger.warning(f"画像検証エラー: {str(e)}")
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "code": e.error_code,
                        "message": e.message
                    }
                }
            )
        except ServerException as e:
            logger.error(f"サーバーエラー: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": e.error_code,
                        "message": e.message
                    }
                }
            )
        except Exception as e:
            logger.error(f"予期せぬエラー: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": ErrorCode.INTERNAL_ERROR,
                        "message": "予期せぬエラーが発生しました"
                    }
                }
            )

# ミドルウェア関数
async def error_handler_middleware(request: Request, call_next):
    middleware = ErrorHandlerMiddleware(call_next)
    return await middleware.dispatch(request) 