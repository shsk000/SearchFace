"""
Tests for core exceptions module
"""
import pytest
from src.core.exceptions import BaseException, ImageValidationException, ServerException
from src.core.errors import ErrorCode


class TestBaseException:
    """Test class for BaseException"""

    @pytest.mark.unit
    def test_base_exception_creation(self):
        """Test BaseException creation with all parameters"""
        code = "TEST_ERROR"
        message = "Test error message"
        status_code = 400
        
        exc = BaseException(code, message, status_code)
        
        assert exc.code == code
        assert exc.message == message
        assert exc.status_code == status_code
        assert str(exc) == message

    @pytest.mark.unit
    def test_base_exception_default_status_code(self):
        """Test BaseException with default status code"""
        code = "TEST_ERROR"
        message = "Test error message"
        
        exc = BaseException(code, message)
        
        assert exc.code == code
        assert exc.message == message
        assert exc.status_code == 500  # Default value

    @pytest.mark.unit
    def test_base_exception_inheritance(self):
        """Test that BaseException inherits from Exception"""
        exc = BaseException("TEST", "Test message")
        assert isinstance(exc, Exception)

    @pytest.mark.unit
    def test_base_exception_attributes_immutable(self):
        """Test that BaseException attributes are accessible"""
        code = "TEST_ERROR"
        message = "Test error message"
        status_code = 422
        
        exc = BaseException(code, message, status_code)
        
        # Should be able to access all attributes
        assert hasattr(exc, 'code')
        assert hasattr(exc, 'message')
        assert hasattr(exc, 'status_code')


class TestImageValidationException:
    """Test class for ImageValidationException"""

    @pytest.mark.unit
    def test_image_validation_exception_creation(self):
        """Test ImageValidationException creation with all parameters"""
        code = ErrorCode.INVALID_IMAGE_FORMAT
        message = "Custom validation message"
        status_code = 422
        
        exc = ImageValidationException(code, message, status_code)
        
        assert exc.code == code
        assert exc.message == message
        assert exc.status_code == status_code

    @pytest.mark.unit
    def test_image_validation_exception_default_message(self):
        """Test ImageValidationException with default message"""
        code = ErrorCode.IMAGE_TOO_LARGE
        
        exc = ImageValidationException(code)
        
        assert exc.code == code
        assert exc.message == "画像の検証に失敗しました"
        assert exc.status_code == 400  # Default value

    @pytest.mark.unit
    def test_image_validation_exception_default_status_code(self):
        """Test ImageValidationException with default status code"""
        code = ErrorCode.NO_FACE_DETECTED
        message = "Custom message"
        
        exc = ImageValidationException(code, message)
        
        assert exc.code == code
        assert exc.message == message
        assert exc.status_code == 400  # Default value

    @pytest.mark.unit
    def test_image_validation_exception_inheritance(self):
        """Test that ImageValidationException inherits from BaseException"""
        exc = ImageValidationException(ErrorCode.IMAGE_CORRUPTED)
        assert isinstance(exc, BaseException)
        assert isinstance(exc, Exception)

    @pytest.mark.unit
    def test_image_validation_exception_all_error_codes(self):
        """Test ImageValidationException with all image-related error codes"""
        image_error_codes = [
            ErrorCode.INVALID_IMAGE_FORMAT,
            ErrorCode.IMAGE_TOO_LARGE,
            ErrorCode.IMAGE_CORRUPTED,
            ErrorCode.NO_FACE_DETECTED,
            ErrorCode.MULTIPLE_FACES
        ]
        
        for code in image_error_codes:
            exc = ImageValidationException(code)
            assert exc.code == code
            assert exc.status_code == 400
            assert exc.message == "画像の検証に失敗しました"

    @pytest.mark.unit
    def test_image_validation_exception_custom_message_override(self):
        """Test that custom message overrides default"""
        code = ErrorCode.INVALID_IMAGE_FORMAT
        custom_message = "This is a custom error message"
        
        exc = ImageValidationException(code, custom_message)
        
        assert exc.message == custom_message
        assert exc.message != "画像の検証に失敗しました"


class TestServerException:
    """Test class for ServerException"""

    @pytest.mark.unit
    def test_server_exception_creation(self):
        """Test ServerException creation with all parameters"""
        code = ErrorCode.INTERNAL_ERROR
        message = "Custom server error message"
        status_code = 503
        
        exc = ServerException(code, message, status_code)
        
        assert exc.code == code
        assert exc.message == message
        assert exc.status_code == status_code

    @pytest.mark.unit
    def test_server_exception_default_values(self):
        """Test ServerException with all default values"""
        exc = ServerException()
        
        assert exc.code == ErrorCode.SERVER_ERROR
        assert exc.message == "サーバーエラーが発生しました"
        assert exc.status_code == 500

    @pytest.mark.unit
    def test_server_exception_default_message(self):
        """Test ServerException with default message"""
        code = ErrorCode.INTERNAL_ERROR
        
        exc = ServerException(code)
        
        assert exc.code == code
        assert exc.message == "サーバーエラーが発生しました"
        assert exc.status_code == 500

    @pytest.mark.unit
    def test_server_exception_default_status_code(self):
        """Test ServerException with default status code"""
        code = ErrorCode.SERVICE_UNAVAILABLE
        message = "Service is temporarily unavailable"
        
        exc = ServerException(code, message)
        
        assert exc.code == code
        assert exc.message == message
        assert exc.status_code == 500

    @pytest.mark.unit
    def test_server_exception_inheritance(self):
        """Test that ServerException inherits from BaseException"""
        exc = ServerException()
        assert isinstance(exc, BaseException)
        assert isinstance(exc, Exception)

    @pytest.mark.unit
    def test_server_exception_all_server_error_codes(self):
        """Test ServerException with all server-related error codes"""
        server_error_codes = [
            ErrorCode.SERVER_ERROR,
            ErrorCode.INTERNAL_ERROR,
            ErrorCode.SERVICE_UNAVAILABLE,
            ErrorCode.DATABASE_ERROR,
            ErrorCode.DATABASE_CONNECTION_ERROR,
            ErrorCode.DATABASE_QUERY_ERROR
        ]
        
        for code in server_error_codes:
            exc = ServerException(code)
            assert exc.code == code
            assert exc.status_code == 500
            assert exc.message == "サーバーエラーが発生しました"

    @pytest.mark.unit
    def test_server_exception_custom_message_override(self):
        """Test that custom message overrides default"""
        code = ErrorCode.INTERNAL_ERROR
        custom_message = "Specific internal error occurred"
        
        exc = ServerException(code, custom_message)
        
        assert exc.message == custom_message
        assert exc.message != "サーバーエラーが発生しました"


class TestExceptionInteraction:
    """Test class for exception interactions and edge cases"""

    @pytest.mark.unit
    def test_exception_string_representation(self):
        """Test string representation of exceptions"""
        message = "Test error occurred"
        
        base_exc = BaseException("TEST", message)
        img_exc = ImageValidationException(ErrorCode.INVALID_IMAGE_FORMAT, message)
        server_exc = ServerException(ErrorCode.SERVER_ERROR, message)
        
        assert str(base_exc) == message
        assert str(img_exc) == message
        assert str(server_exc) == message

    @pytest.mark.unit
    def test_exception_equality(self):
        """Test that exceptions with same parameters are equal in content"""
        code = ErrorCode.INVALID_IMAGE_FORMAT
        message = "Same message"
        status_code = 400
        
        exc1 = ImageValidationException(code, message, status_code)
        exc2 = ImageValidationException(code, message, status_code)
        
        # They should have the same attributes
        assert exc1.code == exc2.code
        assert exc1.message == exc2.message
        assert exc1.status_code == exc2.status_code

    @pytest.mark.unit
    def test_exception_with_none_message(self):
        """Test exceptions when message is explicitly None"""
        img_exc = ImageValidationException(ErrorCode.INVALID_IMAGE_FORMAT, None)
        server_exc = ServerException(ErrorCode.SERVER_ERROR, None)
        
        assert img_exc.message == "画像の検証に失敗しました"
        assert server_exc.message == "サーバーエラーが発生しました"

    @pytest.mark.unit
    def test_exception_with_empty_string_message(self):
        """Test exceptions with empty string message"""
        empty_message = ""
        
        base_exc = BaseException("TEST", empty_message)
        img_exc = ImageValidationException(ErrorCode.INVALID_IMAGE_FORMAT, empty_message)
        server_exc = ServerException(ErrorCode.SERVER_ERROR, empty_message)
        
        assert base_exc.message == empty_message
        assert img_exc.message == empty_message
        assert server_exc.message == empty_message

    @pytest.mark.unit
    def test_exception_attribute_types(self):
        """Test that exception attributes have correct types"""
        exc = ImageValidationException(ErrorCode.INVALID_IMAGE_FORMAT, "Test message", 422)
        
        assert isinstance(exc.code, str)
        assert isinstance(exc.message, str)
        assert isinstance(exc.status_code, int)