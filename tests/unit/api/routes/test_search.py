"""
Tests for search API routes
"""
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import UploadFile
import io
from PIL import Image
import numpy as np

from src.api.main import app
from src.core.errors import ErrorCode
from src.core.exceptions import ImageValidationException, ServerException


class TestSearchRoutes:
    """Test class for search route endpoints"""

    @pytest.fixture
    def client(self):
        """Test client fixture"""
        return TestClient(app)

    @pytest.fixture
    def sample_image_bytes(self):
        """Create sample image bytes for testing"""
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        return img_bytes.getvalue()

    @pytest.fixture
    def large_image_bytes(self):
        """Create large image bytes for testing size validation"""
        # Create a larger image that exceeds 500KB
        img = Image.new('RGB', (1500, 1500), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG', quality=100)
        
        # Ensure the image exceeds 500KB by adding extra data if needed
        current_size = len(img_bytes.getvalue())
        if current_size <= 500 * 1024:
            # Add random data to exceed 500KB
            img_bytes.write(b'x' * (500 * 1024 + 1000 - current_size))
        
        img_bytes.seek(0)
        return img_bytes.getvalue()

    @pytest.mark.unit
    @patch('src.api.routes.search.is_sync_complete', return_value=True)
    @patch('src.api.routes.search.RankingDatabase')
    @patch('src.api.routes.search.SearchDatabase')
    @patch('src.api.routes.search.FaceDatabase')
    @patch('src.api.routes.search.face_utils.get_face_encoding_from_array')
    def test_search_face_success(
        self,
        mock_face_encoding,
        mock_face_db,
        mock_search_db,
        mock_ranking_db,
        mock_sync_complete,
        client,
        sample_image_bytes
    ):
        """Test successful face search"""
        # Mock face encoding
        mock_face_encoding.return_value = np.random.random(128)
        
        # Mock database instances
        mock_face_db_instance = MagicMock()
        mock_search_db_instance = MagicMock()
        mock_ranking_db_instance = MagicMock()
        
        mock_face_db.return_value = mock_face_db_instance
        mock_search_db.return_value = mock_search_db_instance
        mock_ranking_db.return_value = mock_ranking_db_instance
        
        # Mock search results
        mock_face_db_instance.search_similar_faces.return_value = [
            {
                "name": "Test Person 1",
                "distance": 0.3,
                "image_path": "/test/path1.jpg",
                "person_id": 1
            },
            {
                "name": "Test Person 2",
                "distance": 0.4,
                "image_path": "/test/path2.jpg",
                "person_id": 2
            }
        ]
        
        # Mock session recording
        mock_search_db_instance.record_search_results.return_value = "test-session-123"
        
        # Make request
        response = client.post(
            "/api/search",
            files={"image": ("test.jpg", sample_image_bytes, "image/jpeg")},
            params={"top_k": 5}
        )
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data
        assert "processing_time" in data
        assert "search_session_id" in data
        assert len(data["results"]) == 2
        assert data["search_session_id"] == "test-session-123"
        
        # Check result structure
        result = data["results"][0]
        assert "name" in result
        assert "similarity" in result
        assert "distance" in result
        assert "image_path" in result
        
        # Verify database calls
        mock_face_db_instance.search_similar_faces.assert_called_once()
        mock_search_db_instance.record_search_results.assert_called_once()
        mock_ranking_db_instance.update_ranking.assert_called_once_with(person_id=1)

    @pytest.mark.unit
    @patch('src.api.routes.search.is_sync_complete', return_value=True)
    def test_search_face_invalid_image_format(self, mock_sync_complete, client):
        """Test search with invalid image format"""
        text_data = b"This is not an image"
        
        response = client.post(
            "/api/search",
            files={"image": ("test.txt", text_data, "text/plain")}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == ErrorCode.INVALID_IMAGE_FORMAT

    @pytest.mark.unit
    @patch('src.api.routes.search.is_sync_complete', return_value=True)
    def test_search_face_image_too_large(self, mock_sync_complete, client, large_image_bytes):
        """Test search with image that's too large"""
        response = client.post(
            "/api/search",
            files={"image": ("large.jpg", large_image_bytes, "image/jpeg")}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == ErrorCode.IMAGE_TOO_LARGE

    @pytest.mark.unit
    @patch('src.api.routes.search.is_sync_complete', return_value=True)
    @patch('src.api.routes.search.face_utils.get_face_encoding_from_array')
    def test_search_face_no_face_detected(self, mock_face_encoding, mock_sync_complete, client, sample_image_bytes):
        """Test search when no face is detected"""
        mock_face_encoding.return_value = None
        
        response = client.post(
            "/api/search",
            files={"image": ("test.jpg", sample_image_bytes, "image/jpeg")}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == ErrorCode.NO_FACE_DETECTED

    @pytest.mark.unit
    @patch('src.api.routes.search.is_sync_complete', return_value=True)
    @patch('src.api.routes.search.FaceDatabase')
    @patch('src.api.routes.search.face_utils.get_face_encoding_from_array')
    def test_search_face_database_error(
        self,
        mock_face_encoding,
        mock_face_db,
        mock_sync_complete,
        client,
        sample_image_bytes
    ):
        """Test search when database error occurs"""
        mock_face_encoding.return_value = np.random.random(128)
        
        mock_face_db_instance = MagicMock()
        mock_face_db.return_value = mock_face_db_instance
        mock_face_db_instance.search_similar_faces.side_effect = Exception("Database error")
        
        response = client.post(
            "/api/search",
            files={"image": ("test.jpg", sample_image_bytes, "image/jpeg")}
        )
        
        assert response.status_code == 500
        data = response.json()
        assert data["error"]["code"] == ErrorCode.INTERNAL_ERROR

    @pytest.mark.unit
    @patch('src.api.routes.search.is_sync_complete', return_value=True)
    @patch('src.api.routes.search.SearchDatabase')
    def test_get_search_session_results_success(self, mock_search_db, mock_sync_complete, client):
        """Test successful retrieval of search session results"""
        mock_search_db_instance = MagicMock()
        mock_search_db.return_value = mock_search_db_instance
        
        # Mock session data
        mock_search_db_instance.get_search_session_results.return_value = {
            'session_id': 'test-session-123',
            'search_timestamp': '2024-01-01 10:00:00',
            'metadata': {'filename': 'test.jpg', 'file_size': 1024},
            'results': [
                {
                    'rank': 1,
                    'person_id': 1,
                    'name': 'Test Person 1',
                    'distance': 0.3,
                    'image_path': '/test/path1.jpg'
                }
            ]
        }
        
        response = client.get("/api/search/test-session-123")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["session_id"] == "test-session-123"
        assert data["search_timestamp"] == "2024-01-01 10:00:00"
        assert "metadata" in data
        assert "results" in data
        assert len(data["results"]) == 1
        
        result = data["results"][0]
        assert result["rank"] == 1
        assert result["person_id"] == 1
        assert result["name"] == "Test Person 1"
        assert "similarity" in result
        assert "distance" in result

    @pytest.mark.unit
    @patch('src.api.routes.search.is_sync_complete', return_value=True)
    @patch('src.api.routes.search.SearchDatabase')
    def test_get_search_session_results_not_found(self, mock_search_db, mock_sync_complete, client):
        """Test retrieval of non-existent search session"""
        mock_search_db_instance = MagicMock()
        mock_search_db.return_value = mock_search_db_instance
        mock_search_db_instance.get_search_session_results.return_value = None
        
        response = client.get("/api/search/non-existent-session")
        
        assert response.status_code == 500
        data = response.json()
        assert data["error"]["code"] == ErrorCode.SESSION_NOT_FOUND

    @pytest.mark.unit
    @patch('src.api.routes.search.is_sync_complete', return_value=True)
    @patch('src.api.routes.search.SearchDatabase')
    def test_get_search_session_database_error(self, mock_search_db, mock_sync_complete, client):
        """Test session retrieval when database error occurs"""
        mock_search_db_instance = MagicMock()
        mock_search_db.return_value = mock_search_db_instance
        mock_search_db_instance.get_search_session_results.side_effect = Exception("Database error")
        
        response = client.get("/api/search/test-session")
        
        assert response.status_code == 500
        data = response.json()
        assert data["error"]["code"] == ErrorCode.INTERNAL_ERROR

    @pytest.mark.unit
    @patch('src.api.routes.search.is_sync_complete', return_value=True)
    def test_search_face_corrupted_image(self, mock_sync_complete, client):
        """Test search with corrupted image data"""
        corrupted_data = b"fake image data that cannot be parsed"
        
        response = client.post(
            "/api/search",
            files={"image": ("corrupted.jpg", corrupted_data, "image/jpeg")}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == ErrorCode.IMAGE_CORRUPTED

    @pytest.mark.unit
    @patch('src.api.routes.search.is_sync_complete', return_value=True)
    @patch('src.api.routes.search.RankingDatabase')
    @patch('src.api.routes.search.SearchDatabase')
    @patch('src.api.routes.search.FaceDatabase')
    @patch('src.api.routes.search.face_utils.get_face_encoding_from_array')
    def test_search_face_database_recording_failure(
        self,
        mock_face_encoding,
        mock_face_db,
        mock_search_db,
        mock_ranking_db,
        mock_sync_complete,
        client,
        sample_image_bytes
    ):
        """Test that search succeeds even if database recording fails"""
        # Mock face encoding
        mock_face_encoding.return_value = np.random.random(128)
        
        # Mock database instances
        mock_face_db_instance = MagicMock()
        mock_search_db_instance = MagicMock()
        mock_ranking_db_instance = MagicMock()
        
        mock_face_db.return_value = mock_face_db_instance
        mock_search_db.return_value = mock_search_db_instance
        mock_ranking_db.return_value = mock_ranking_db_instance
        
        # Ensure close methods are properly mocked to prevent hanging
        mock_face_db_instance.close = MagicMock()
        mock_search_db_instance.close = MagicMock()
        mock_ranking_db_instance.close = MagicMock()
        
        # Mock search results
        mock_face_db_instance.search_similar_faces.return_value = [
            {
                "name": "Test Person 1",
                "distance": 0.3,
                "image_path": "/test/path1.jpg",
                "person_id": 1
            }
        ]
        
        # Mock database recording failure
        mock_search_db_instance.record_search_results.side_effect = Exception("Recording failed")
        
        # Make request
        response = client.post(
            "/api/search",
            files={"image": ("test.jpg", sample_image_bytes, "image/jpeg")}
        )
        
        # Should still succeed with search results
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data
        assert len(data["results"]) == 1
        # Session ID should be empty string when recording fails
        assert data["search_session_id"] == ""

    @pytest.mark.unit
    @patch('src.api.routes.search.is_sync_complete', return_value=True)
    @patch('src.api.routes.search.SearchDatabase')
    @patch('src.api.routes.search.RankingDatabase')
    @patch('src.api.routes.search.FaceDatabase')
    @patch('src.api.routes.search.face_utils.get_face_encoding_from_array')
    def test_search_face_rgba_image_conversion(
        self,
        mock_face_encoding,
        mock_face_db,
        mock_ranking_db,
        mock_search_db,
        mock_sync_complete,
        client
    ):
        """Test search with RGBA image that gets converted to RGB"""
        # Create RGBA image
        img = Image.new('RGBA', (100, 100), color=(255, 0, 0, 128))
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        mock_face_encoding.return_value = np.random.random(128)
        
        # Mock database instances
        mock_face_db_instance = MagicMock()
        mock_search_db_instance = MagicMock()
        mock_ranking_db_instance = MagicMock()
        
        mock_face_db.return_value = mock_face_db_instance
        mock_search_db.return_value = mock_search_db_instance
        mock_ranking_db.return_value = mock_ranking_db_instance
        
        # Ensure close methods are properly mocked to prevent hanging
        mock_face_db_instance.close = MagicMock()
        mock_search_db_instance.close = MagicMock()
        mock_ranking_db_instance.close = MagicMock()
        
        mock_face_db_instance.search_similar_faces.return_value = [
            {
                "name": "Test Person 1",
                "distance": 0.3,
                "image_path": "/test/path1.jpg",
                "person_id": 1
            }
        ]
        
        # Mock successful database recording
        mock_search_db_instance.record_search_results.return_value = "test-session-123"
        
        response = client.post(
            "/api/search",
            files={"image": ("test.png", img_bytes.getvalue(), "image/png")}
        )
        
        assert response.status_code == 200
        # Verify that face encoding was called (image was processed successfully)
        mock_face_encoding.assert_called_once()