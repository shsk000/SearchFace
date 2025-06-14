"""
Tests for face_utils module
"""
import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
from io import BytesIO

from src.face import face_utils
from src.core.exceptions import ImageValidationException
from src.core.errors import ErrorCode


class TestFaceUtils:
    """Test class for face_utils"""

    def test_load_image_from_url_success(self):
        """Test successful image loading from URL"""
        # Create mock image data
        mock_image = Image.new('RGB', (100, 100), color='red')
        mock_image_bytes = BytesIO()
        mock_image.save(mock_image_bytes, format='JPEG')
        mock_image_bytes.seek(0)
        
        with patch('src.face.face_utils.requests.get') as mock_get:
            # Mock successful HTTP response
            mock_response = Mock()
            mock_response.content = mock_image_bytes.getvalue()
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            # Test the function
            result = face_utils.load_image_from_url('http://example.com/test.jpg')
            
            # Verify results
            assert result is not None
            assert isinstance(result, np.ndarray)
            assert result.shape == (100, 100, 3)  # RGB image
            
            # Verify HTTP request was made correctly
            mock_get.assert_called_once_with(
                'http://example.com/test.jpg',
                timeout=30,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )

    def test_load_image_from_url_http_error(self):
        """Test image loading from URL with HTTP error"""
        with patch('src.face.face_utils.requests.get') as mock_get:
            # Mock HTTP error
            mock_get.side_effect = Exception("HTTP 404 Not Found")
            
            # Test the function
            result = face_utils.load_image_from_url('http://example.com/nonexistent.jpg')
            
            # Should return None on error
            assert result is None

    def test_load_image_from_url_invalid_image(self):
        """Test image loading from URL with invalid image data"""
        with patch('src.face.face_utils.requests.get') as mock_get:
            # Mock response with invalid image data
            mock_response = Mock()
            mock_response.content = b'invalid image data'
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            # Test the function
            result = face_utils.load_image_from_url('http://example.com/invalid.jpg')
            
            # Should return None on invalid image
            assert result is None

    def test_load_image_from_url_rgba_conversion(self):
        """Test RGBA to RGB conversion"""
        # Create RGBA image
        mock_image = Image.new('RGBA', (50, 50), color=(255, 0, 0, 128))
        mock_image_bytes = BytesIO()
        mock_image.save(mock_image_bytes, format='PNG')
        mock_image_bytes.seek(0)
        
        with patch('src.face.face_utils.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.content = mock_image_bytes.getvalue()
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            result = face_utils.load_image_from_url('http://example.com/rgba.png')
            
            # Should convert to RGB (3 channels)
            assert result is not None
            assert result.shape == (50, 50, 3)

    def test_load_image_url_delegation(self):
        """Test that load_image delegates to load_image_from_url for URLs"""
        with patch('src.face.face_utils.load_image_from_url') as mock_load_url:
            mock_load_url.return_value = np.array([[[255, 0, 0]]])
            
            result = face_utils.load_image('http://example.com/test.jpg')
            
            # Should delegate to load_image_from_url
            mock_load_url.assert_called_once_with('http://example.com/test.jpg')
            assert result is not None

    def test_load_image_local_file(self):
        """Test that load_image uses face_recognition.load_image_file for local files"""
        with patch('src.face.face_utils.face_recognition.load_image_file') as mock_load_file:
            mock_load_file.return_value = np.array([[[0, 255, 0]]])
            
            result = face_utils.load_image('/path/to/local/file.jpg')
            
            # Should use face_recognition.load_image_file
            mock_load_file.assert_called_once_with('/path/to/local/file.jpg')
            assert result is not None

    def test_load_image_local_file_error(self):
        """Test load_image error handling for local files"""
        with patch('src.face.face_utils.face_recognition.load_image_file') as mock_load_file:
            mock_load_file.side_effect = Exception("File not found")
            
            result = face_utils.load_image('/nonexistent/file.jpg')
            
            # Should return None on error
            assert result is None

    def test_get_face_encoding_url_success(self):
        """Test get_face_encoding with URL input"""
        mock_image = np.random.rand(100, 100, 3)
        mock_encoding = np.random.rand(128).astype(np.float32)
        
        with patch('src.face.face_utils.load_image_from_url') as mock_load_url, \
             patch('src.face.face_utils.detect_faces') as mock_detect:
            
            mock_load_url.return_value = mock_image
            mock_detect.return_value = ([mock_encoding], [(0, 50, 50, 0)])
            
            result = face_utils.get_face_encoding('http://example.com/face.jpg')
            
            # Should return the encoding
            assert result is not None
            np.testing.assert_array_equal(result, mock_encoding)
            mock_load_url.assert_called_once_with('http://example.com/face.jpg')

    def test_get_face_encoding_local_file_success(self):
        """Test get_face_encoding with local file input"""
        mock_image = np.random.rand(100, 100, 3)
        mock_encoding = np.random.rand(128).astype(np.float32)
        
        with patch('src.face.face_utils.face_recognition.load_image_file') as mock_load_file, \
             patch('src.face.face_utils.detect_faces') as mock_detect:
            
            mock_load_file.return_value = mock_image
            mock_detect.return_value = ([mock_encoding], [(0, 50, 50, 0)])
            
            result = face_utils.get_face_encoding('/path/to/face.jpg')
            
            # Should return the encoding
            assert result is not None
            np.testing.assert_array_equal(result, mock_encoding)
            mock_load_file.assert_called_once_with('/path/to/face.jpg')

    def test_get_face_encoding_no_faces(self):
        """Test get_face_encoding when no faces are detected"""
        mock_image = np.random.rand(100, 100, 3)
        
        with patch('src.face.face_utils.load_image') as mock_load, \
             patch('src.face.face_utils.detect_faces') as mock_detect:
            
            mock_load.return_value = mock_image
            mock_detect.return_value = ([], [])  # No faces detected
            
            result = face_utils.get_face_encoding('http://example.com/no_face.jpg')
            
            # Should return None when no faces detected
            assert result is None

    def test_get_face_encoding_multiple_faces(self):
        """Test get_face_encoding when multiple faces are detected"""
        mock_image = np.random.rand(100, 100, 3)
        mock_encoding1 = np.random.rand(128).astype(np.float32)
        mock_encoding2 = np.random.rand(128).astype(np.float32)
        
        with patch('src.face.face_utils.load_image_from_url') as mock_load_url, \
             patch('src.face.face_utils.detect_faces') as mock_detect:
            
            mock_load_url.return_value = mock_image
            mock_detect.return_value = ([mock_encoding1, mock_encoding2], [(0, 25, 25, 0), (50, 75, 75, 50)])
            
            # Should raise exception for multiple faces
            with pytest.raises(ImageValidationException):
                face_utils.get_face_encoding('http://example.com/multiple_faces.jpg')

    def test_get_face_encoding_image_load_failure(self):
        """Test get_face_encoding when image loading fails"""
        with patch('src.face.face_utils.load_image') as mock_load:
            mock_load.return_value = None  # Image loading failed
            
            result = face_utils.get_face_encoding('http://example.com/invalid.jpg')
            
            # Should return None when image loading fails
            assert result is None

    def test_detect_faces_basic_functionality(self):
        """Test basic detect_faces functionality"""
        mock_image = np.random.rand(100, 100, 3)
        mock_locations = [(10, 60, 60, 10)]
        mock_encodings = [np.random.rand(128).astype(np.float32)]
        
        with patch('src.face.face_utils.face_recognition.face_locations') as mock_locations_func, \
             patch('src.face.face_utils.face_recognition.face_encodings') as mock_encodings_func:
            
            mock_locations_func.return_value = mock_locations
            mock_encodings_func.return_value = mock_encodings
            
            encodings, locations = face_utils.detect_faces(mock_image)
            
            # Verify function calls
            mock_locations_func.assert_called_once_with(mock_image)
            mock_encodings_func.assert_called_once_with(mock_image, mock_locations)
            
            # Verify results
            assert encodings == mock_encodings
            assert locations == mock_locations

    def test_get_face_encoding_from_array_success(self):
        """Test get_face_encoding_from_array with single face"""
        mock_image = np.random.rand(100, 100, 3)
        mock_encoding = np.random.rand(128).astype(np.float32)
        
        with patch('src.face.face_utils.detect_faces') as mock_detect:
            mock_detect.return_value = ([mock_encoding], [(0, 50, 50, 0)])
            
            result = face_utils.get_face_encoding_from_array(mock_image)
            
            # Should return the encoding
            assert result is not None
            np.testing.assert_array_equal(result, mock_encoding)

    def test_get_face_encoding_from_array_no_faces(self):
        """Test get_face_encoding_from_array with no faces"""
        mock_image = np.random.rand(100, 100, 3)
        
        with patch('src.face.face_utils.detect_faces') as mock_detect:
            mock_detect.return_value = ([], [])
            
            result = face_utils.get_face_encoding_from_array(mock_image)
            
            # Should return None
            assert result is None

    def test_get_face_encoding_from_array_multiple_faces(self):
        """Test get_face_encoding_from_array with multiple faces"""
        mock_image = np.random.rand(100, 100, 3)
        mock_encoding1 = np.random.rand(128).astype(np.float32)
        mock_encoding2 = np.random.rand(128).astype(np.float32)
        
        with patch('src.face.face_utils.detect_faces') as mock_detect:
            mock_detect.return_value = ([mock_encoding1, mock_encoding2], [(0, 25, 25, 0), (50, 75, 75, 50)])
            
            # Should raise exception for multiple faces
            with pytest.raises(ImageValidationException):
                face_utils.get_face_encoding_from_array(mock_image)