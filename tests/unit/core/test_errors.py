"""
Tests for core errors module
"""
import pytest
from src.core.errors import ErrorCode, ERROR_MESSAGES, get_error_response


class TestErrorCode:
    """Test class for ErrorCode enum"""

    @pytest.mark.unit
    def test_error_code_values(self):
        """Test that error codes have expected string values"""
        assert ErrorCode.INVALID_IMAGE_FORMAT == "INVALID_IMAGE_FORMAT"
        assert ErrorCode.IMAGE_TOO_LARGE == "IMAGE_TOO_LARGE"
        assert ErrorCode.IMAGE_CORRUPTED == "IMAGE_CORRUPTED"
        assert ErrorCode.NO_FACE_DETECTED == "NO_FACE_DETECTED"
        assert ErrorCode.MULTIPLE_FACES == "MULTIPLE_FACES"
        
        assert ErrorCode.DATABASE_ERROR == "DATABASE_ERROR"
        assert ErrorCode.DATABASE_CONNECTION_ERROR == "DATABASE_CONNECTION_ERROR"
        assert ErrorCode.DATABASE_QUERY_ERROR == "DATABASE_QUERY_ERROR"
        
        assert ErrorCode.SERVER_ERROR == "SERVER_ERROR"
        assert ErrorCode.INTERNAL_ERROR == "INTERNAL_ERROR"
        assert ErrorCode.SERVICE_UNAVAILABLE == "SERVICE_UNAVAILABLE"
        
        assert ErrorCode.SESSION_NOT_FOUND == "SESSION_NOT_FOUND"

    @pytest.mark.unit
    def test_error_code_inheritance(self):
        """Test that ErrorCode inherits from str and Enum"""
        assert isinstance(ErrorCode.INVALID_IMAGE_FORMAT, str)
        assert hasattr(ErrorCode, '__members__')

    @pytest.mark.unit
    def test_all_error_codes_have_messages(self):
        """Test that all error codes have corresponding messages"""
        for error_code in ErrorCode:
            assert error_code in ERROR_MESSAGES
            assert isinstance(ERROR_MESSAGES[error_code], str)
            assert len(ERROR_MESSAGES[error_code]) > 0


class TestErrorMessages:
    """Test class for ERROR_MESSAGES"""

    @pytest.mark.unit
    def test_error_messages_content(self):
        """Test that error messages contain expected content"""
        assert "無効な画像形式" in ERROR_MESSAGES[ErrorCode.INVALID_IMAGE_FORMAT]
        assert "500KB" in ERROR_MESSAGES[ErrorCode.IMAGE_TOO_LARGE]
        assert "破損" in ERROR_MESSAGES[ErrorCode.IMAGE_CORRUPTED]
        assert "顔が検出できませんでした" in ERROR_MESSAGES[ErrorCode.NO_FACE_DETECTED]
        assert "複数の顔" in ERROR_MESSAGES[ErrorCode.MULTIPLE_FACES]
        
        assert "データベースエラー" in ERROR_MESSAGES[ErrorCode.DATABASE_ERROR]
        assert "接続に失敗" in ERROR_MESSAGES[ErrorCode.DATABASE_CONNECTION_ERROR]
        assert "クエリの実行に失敗" in ERROR_MESSAGES[ErrorCode.DATABASE_QUERY_ERROR]
        
        assert "サーバーエラー" in ERROR_MESSAGES[ErrorCode.SERVER_ERROR]
        assert "内部エラー" in ERROR_MESSAGES[ErrorCode.INTERNAL_ERROR]
        assert "利用できません" in ERROR_MESSAGES[ErrorCode.SERVICE_UNAVAILABLE]
        
        assert "見つかりません" in ERROR_MESSAGES[ErrorCode.SESSION_NOT_FOUND]

    @pytest.mark.unit
    def test_error_messages_are_japanese(self):
        """Test that all error messages are in Japanese"""
        import unicodedata
        
        for message in ERROR_MESSAGES.values():
            # Check if message contains at least one Japanese character (hiragana/katakana/kanji)
            has_japanese = any(
                unicodedata.name(char, '').startswith(('HIRAGANA', 'KATAKANA', 'CJK UNIFIED IDEOGRAPH'))
                for char in message
            )
            assert has_japanese, f"Message '{message}' does not contain Japanese characters"


class TestGetErrorResponse:
    """Test class for get_error_response function"""

    @pytest.mark.unit
    def test_get_error_response_valid_code(self):
        """Test get_error_response with valid error code"""
        response = get_error_response(ErrorCode.INVALID_IMAGE_FORMAT)
        
        assert "error" in response
        assert "code" in response["error"]
        assert "message" in response["error"]
        
        assert response["error"]["code"] == ErrorCode.INVALID_IMAGE_FORMAT
        assert response["error"]["message"] == ERROR_MESSAGES[ErrorCode.INVALID_IMAGE_FORMAT]

    @pytest.mark.unit
    def test_get_error_response_all_codes(self):
        """Test get_error_response with all error codes"""
        for error_code in ErrorCode:
            response = get_error_response(error_code)
            
            assert isinstance(response, dict)
            assert "error" in response
            assert response["error"]["code"] == error_code
            assert response["error"]["message"] == ERROR_MESSAGES[error_code]

    @pytest.mark.unit
    def test_get_error_response_structure(self):
        """Test that get_error_response returns correct structure"""
        response = get_error_response(ErrorCode.SERVER_ERROR)
        
        # Check top-level structure
        assert len(response) == 1
        assert "error" in response
        
        # Check error object structure
        error_obj = response["error"]
        assert len(error_obj) == 2
        assert "code" in error_obj
        assert "message" in error_obj
        
        # Check data types
        assert isinstance(error_obj["code"], str)
        assert isinstance(error_obj["message"], str)

    @pytest.mark.unit
    def test_get_error_response_unknown_code(self):
        """Test get_error_response with unknown error code"""
        # Create a mock error code that doesn't exist in ERROR_MESSAGES
        unknown_code = "UNKNOWN_ERROR_CODE"
        response = get_error_response(unknown_code)
        
        assert response["error"]["code"] == unknown_code
        assert response["error"]["message"] == "不明なエラーが発生しました"

    @pytest.mark.unit
    def test_get_error_response_immutability(self):
        """Test that get_error_response doesn't modify original ERROR_MESSAGES"""
        original_messages = ERROR_MESSAGES.copy()
        
        # Call function multiple times
        for error_code in ErrorCode:
            get_error_response(error_code)
        
        # Verify original dictionary wasn't modified
        assert ERROR_MESSAGES == original_messages

    @pytest.mark.unit
    def test_error_response_serializable(self):
        """Test that error response is JSON serializable"""
        import json
        
        for error_code in ErrorCode:
            response = get_error_response(error_code)
            
            # Should not raise exception
            json_str = json.dumps(response)
            
            # Should be able to parse back
            parsed = json.loads(json_str)
            assert parsed == response