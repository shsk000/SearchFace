from fastapi import HTTPException, status
from src.core.errors import ErrorCode, get_error_response

class SearchFaceException(HTTPException):
    def __init__(self, error_code: ErrorCode, status_code: int = status.HTTP_400_BAD_REQUEST):
        error_response = get_error_response(error_code)
        super().__init__(
            status_code=status_code,
            detail=error_response["error"]
        )

class ImageValidationException(SearchFaceException):
    def __init__(self, error_code: ErrorCode):
        super().__init__(error_code, status.HTTP_400_BAD_REQUEST)

class ServerException(SearchFaceException):
    def __init__(self, error_code: ErrorCode):
        super().__init__(error_code, status.HTTP_500_INTERNAL_SERVER_ERROR) 