"""
Tests for core middleware module
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import json
from fastapi import Request
from starlette.responses import JSONResponse

from src.core.middleware import ErrorHandlerMiddleware, error_handler_middleware
from src.core.exceptions import BaseException, ImageValidationException, ServerException
from src.core.errors import ErrorCode


class TestErrorHandlerMiddleware:
    """Test class for ErrorHandlerMiddleware"""

    @pytest.fixture
    def middleware(self):
        """Create middleware instance"""
        app = Mock()
        return ErrorHandlerMiddleware(app)

    @pytest.fixture
    def mock_request(self):
        """Create mock request"""
        request = Mock(spec=Request)
        return request

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_middleware_success_response(self, middleware, mock_request):
        """Test middleware with successful response"""
        # Mock successful call_next
        mock_response = Mock()
        call_next = AsyncMock(return_value=mock_response)
        
        result = await middleware.dispatch(mock_request, call_next)
        
        assert result == mock_response
        call_next.assert_called_once_with(mock_request)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_middleware_base_exception_handling(self, middleware, mock_request):
        """Test middleware handling of BaseException"""
        # Mock call_next to raise BaseException
        test_exception = BaseException(
            code=ErrorCode.INVALID_IMAGE_FORMAT,
            message="Test error message",
            status_code=422
        )
        call_next = AsyncMock(side_effect=test_exception)
        
        with patch('src.core.middleware.logger') as mock_logger:
            result = await middleware.dispatch(mock_request, call_next)
        
        # Check that it returns JSONResponse
        assert isinstance(result, JSONResponse)
        assert result.status_code == 422
        
        # Parse response content
        content = json.loads(result.body.decode())
        assert content["error"]["code"] == ErrorCode.INVALID_IMAGE_FORMAT
        assert content["error"]["message"] == "Test error message"
        
        # Check logging
        mock_logger.error.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_middleware_image_validation_exception(self, middleware, mock_request):
        """Test middleware handling of ImageValidationException"""
        test_exception = ImageValidationException(
            code=ErrorCode.NO_FACE_DETECTED,
            message="No face detected",
            status_code=400
        )
        call_next = AsyncMock(side_effect=test_exception)
        
        result = await middleware.dispatch(mock_request, call_next)
        
        assert isinstance(result, JSONResponse)
        assert result.status_code == 400
        
        content = json.loads(result.body.decode())
        assert content["error"]["code"] == ErrorCode.NO_FACE_DETECTED
        assert content["error"]["message"] == "No face detected"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_middleware_server_exception(self, middleware, mock_request):
        """Test middleware handling of ServerException"""
        test_exception = ServerException(
            code=ErrorCode.INTERNAL_ERROR,
            message="Internal server error",
            status_code=500
        )
        call_next = AsyncMock(side_effect=test_exception)
        
        result = await middleware.dispatch(mock_request, call_next)
        
        assert isinstance(result, JSONResponse)
        assert result.status_code == 500
        
        content = json.loads(result.body.decode())
        assert content["error"]["code"] == ErrorCode.INTERNAL_ERROR
        assert content["error"]["message"] == "Internal server error"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_middleware_generic_exception_handling(self, middleware, mock_request):
        """Test middleware handling of generic Exception"""
        test_exception = Exception("Unexpected error")
        call_next = AsyncMock(side_effect=test_exception)
        
        with patch('src.core.middleware.logger') as mock_logger:
            result = await middleware.dispatch(mock_request, call_next)
        
        assert isinstance(result, JSONResponse)
        assert result.status_code == 500
        
        content = json.loads(result.body.decode())
        assert content["error"]["code"] == ErrorCode.SERVER_ERROR
        assert content["error"]["message"] == "サーバーエラーが発生しました"
        
        # Check logging
        mock_logger.error.assert_called_once()
        assert "予期せぬエラーが発生しました" in str(mock_logger.error.call_args)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_middleware_response_structure(self, middleware, mock_request):
        """Test that error response has correct structure"""
        test_exception = BaseException("TEST_ERROR", "Test message", 400)
        call_next = AsyncMock(side_effect=test_exception)
        
        result = await middleware.dispatch(mock_request, call_next)
        
        content = json.loads(result.body.decode())
        
        # Check structure
        assert "error" in content
        assert len(content) == 1
        
        error_obj = content["error"]
        assert "code" in error_obj
        assert "message" in error_obj
        assert len(error_obj) == 2


class TestErrorHandlerMiddlewareFunction:
    """Test class for error_handler_middleware function"""

    @pytest.fixture
    def mock_request(self):
        """Create mock request"""
        request = Mock(spec=Request)
        return request

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_function_success_response(self, mock_request):
        """Test middleware function with successful response"""
        mock_response = Mock()
        call_next = AsyncMock(return_value=mock_response)
        
        result = await error_handler_middleware(mock_request, call_next)
        
        assert result == mock_response
        call_next.assert_called_once_with(mock_request)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_function_base_exception_handling(self, mock_request):
        """Test middleware function handling of BaseException"""
        test_exception = BaseException(
            code=ErrorCode.DATABASE_ERROR,
            message="Database connection failed",
            status_code=503
        )
        call_next = AsyncMock(side_effect=test_exception)
        
        with patch('src.core.middleware.logger') as mock_logger:
            result = await error_handler_middleware(mock_request, call_next)
        
        assert isinstance(result, JSONResponse)
        assert result.status_code == 503
        
        content = json.loads(result.body.decode())
        assert content["error"]["code"] == ErrorCode.DATABASE_ERROR
        assert content["error"]["message"] == "Database connection failed"
        
        mock_logger.error.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_function_generic_exception_handling(self, mock_request):
        """Test middleware function handling of generic Exception"""
        test_exception = ValueError("Invalid value")
        call_next = AsyncMock(side_effect=test_exception)
        
        with patch('src.core.middleware.logger') as mock_logger:
            result = await error_handler_middleware(mock_request, call_next)
        
        assert isinstance(result, JSONResponse)
        assert result.status_code == 500
        
        content = json.loads(result.body.decode())
        assert content["error"]["code"] == ErrorCode.SERVER_ERROR
        assert content["error"]["message"] == "サーバーエラーが発生しました"
        
        mock_logger.error.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_function_multiple_calls(self, mock_request):
        """Test middleware function with multiple calls"""
        # First call succeeds
        success_response = Mock()
        call_next_success = AsyncMock(return_value=success_response)
        
        result1 = await error_handler_middleware(mock_request, call_next_success)
        assert result1 == success_response
        
        # Second call fails
        test_exception = BaseException("ERROR", "Error message", 400)
        call_next_error = AsyncMock(side_effect=test_exception)
        
        result2 = await error_handler_middleware(mock_request, call_next_error)
        assert isinstance(result2, JSONResponse)
        assert result2.status_code == 400


class TestMiddlewareIntegration:
    """Test class for middleware integration scenarios"""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_nested_exceptions(self):
        """Test middleware with nested exceptions"""
        inner_exception = ValueError("Inner error")
        outer_exception = BaseException(
            code=ErrorCode.INTERNAL_ERROR,
            message="Outer error",
            status_code=500
        )
        
        # Mock call_next that raises the outer exception
        call_next = AsyncMock(side_effect=outer_exception)
        mock_request = Mock(spec=Request)
        
        result = await error_handler_middleware(mock_request, call_next)
        
        assert isinstance(result, JSONResponse)
        assert result.status_code == 500
        
        content = json.loads(result.body.decode())
        assert content["error"]["code"] == ErrorCode.INTERNAL_ERROR
        assert content["error"]["message"] == "Outer error"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_exception_with_complex_message(self):
        """Test middleware with exception containing complex message"""
        complex_message = "Error occurred with data: {'key': 'value', 'number': 123}"
        test_exception = BaseException(
            code=ErrorCode.INTERNAL_ERROR,
            message=complex_message,
            status_code=500
        )
        
        call_next = AsyncMock(side_effect=test_exception)
        mock_request = Mock(spec=Request)
        
        result = await error_handler_middleware(mock_request, call_next)
        
        content = json.loads(result.body.decode())
        assert content["error"]["message"] == complex_message

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_all_error_codes_handled(self):
        """Test that all error codes are properly handled"""
        mock_request = Mock(spec=Request)
        
        error_codes = [
            ErrorCode.INVALID_IMAGE_FORMAT,
            ErrorCode.IMAGE_TOO_LARGE,
            ErrorCode.NO_FACE_DETECTED,
            ErrorCode.DATABASE_ERROR,
            ErrorCode.SERVER_ERROR,
            ErrorCode.SESSION_NOT_FOUND
        ]
        
        for error_code in error_codes:
            test_exception = BaseException(
                code=error_code,
                message=f"Test message for {error_code}",
                status_code=400
            )
            call_next = AsyncMock(side_effect=test_exception)
            
            result = await error_handler_middleware(mock_request, call_next)
            
            assert isinstance(result, JSONResponse)
            content = json.loads(result.body.decode())
            assert content["error"]["code"] == error_code

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_unicode_error_messages(self):
        """Test middleware with Unicode characters in error messages"""
        unicode_message = "エラーが発生しました: データベース接続に失敗 🚫"
        test_exception = BaseException(
            code=ErrorCode.DATABASE_ERROR,
            message=unicode_message,
            status_code=500
        )
        
        call_next = AsyncMock(side_effect=test_exception)
        mock_request = Mock(spec=Request)
        
        result = await error_handler_middleware(mock_request, call_next)
        
        content = json.loads(result.body.decode())
        assert content["error"]["message"] == unicode_message

    @pytest.mark.unit
    def test_middleware_initialization(self):
        """Test ErrorHandlerMiddleware initialization"""
        app = Mock()
        middleware = ErrorHandlerMiddleware(app)
        
        assert middleware.app == app
        assert hasattr(middleware, 'dispatch')

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_logging_behavior(self):
        """Test that proper logging occurs for different exception types"""
        mock_request = Mock(spec=Request)
        
        # Test BaseException logging
        base_exception = BaseException("TEST", "Base error", 400)
        call_next = AsyncMock(side_effect=base_exception)
        
        with patch('src.core.middleware.logger') as mock_logger:
            await error_handler_middleware(mock_request, call_next)
            mock_logger.error.assert_called_once()
            assert "エラーが発生しました" in str(mock_logger.error.call_args)
        
        # Test generic Exception logging
        generic_exception = Exception("Generic error")
        call_next = AsyncMock(side_effect=generic_exception)
        
        with patch('src.core.middleware.logger') as mock_logger:
            await error_handler_middleware(mock_request, call_next)
            mock_logger.error.assert_called_once()
            assert "予期せぬエラーが発生しました" in str(mock_logger.error.call_args)