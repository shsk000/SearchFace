"""
Integration tests for API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import io
from PIL import Image

from src.api.main import app


class TestAPIIntegration:
    """Integration test class for API endpoints"""

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

    @pytest.mark.integration
    @patch('src.api.routes.search.RankingDatabase')
    @patch('src.api.routes.search.SearchDatabase')
    @patch('src.api.routes.search.FaceDatabase')
    @patch('src.api.routes.search.face_utils.get_face_encoding_from_array')
    def test_full_search_workflow(
        self,
        mock_face_encoding,
        mock_face_db,
        mock_search_db,
        mock_ranking_db,
        client,
        sample_image_bytes
    ):
        """Test complete search workflow from upload to response"""
        # Setup mocks
        import numpy as np
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
            }
        ]
        
        # Mock session recording
        mock_search_db_instance.record_search_results.return_value = "integration-session-123"
        
        # Execute search
        response = client.post(
            "/api/search",
            files={"image": ("test.jpg", sample_image_bytes, "image/jpeg")},
            params={"top_k": 5}
        )
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data
        assert "processing_time" in data
        assert "search_session_id" in data
        assert data["search_session_id"] == "integration-session-123"
        
        # Verify database interactions
        mock_face_db_instance.search_similar_faces.assert_called_once()
        mock_search_db_instance.record_search_results.assert_called_once()
        mock_ranking_db_instance.update_ranking.assert_called_once_with(person_id=1)

    @pytest.mark.integration
    @patch('src.api.routes.ranking.RankingDatabase')
    def test_ranking_api_integration(self, mock_ranking_db, client):
        """Test ranking API integration"""
        # Mock ranking database
        mock_ranking_db_instance = MagicMock()
        mock_ranking_db.return_value = mock_ranking_db_instance
        
        # Mock ranking data
        mock_ranking_data = [
            {
                'rank': 1,
                'person_id': 1,
                'name': 'Test Person 1',
                'win_count': 10,
                'search_count': 20,
                'win_rate': 0.5,
                'last_win_date': '2024-01-01 10:00:00',
                'image_path': '/test/path1.jpg'
            }
        ]
        mock_ranking_db_instance.get_ranking.return_value = mock_ranking_data
        
        # Test ranking endpoint
        response = client.get("/api/ranking?limit=5")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "ranking" in data
        assert "total_count" in data
        assert data["total_count"] == 1
        
        # Verify database call
        mock_ranking_db_instance.get_ranking.assert_called_once_with(limit=5)

    @pytest.mark.integration
    @patch('src.api.routes.search.SearchDatabase')
    def test_search_session_retrieval_integration(self, mock_search_db, client):
        """Test search session retrieval integration"""
        # Mock search database
        mock_search_db_instance = MagicMock()
        mock_search_db.return_value = mock_search_db_instance
        
        # Mock session data
        mock_search_db_instance.get_search_session_results.return_value = {
            'session_id': 'integration-session-123',
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
        
        # Test session retrieval
        response = client.get("/api/search/integration-session-123")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["session_id"] == "integration-session-123"
        assert "results" in data
        assert len(data["results"]) == 1

    @pytest.mark.integration
    def test_error_handling_integration(self, client):
        """Test error handling across the API"""
        # Test invalid image format
        response = client.post(
            "/api/search",
            files={"image": ("test.txt", b"not an image", "text/plain")}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "INVALID_IMAGE_FORMAT"

    @pytest.mark.integration
    def test_api_documentation_integration(self, client):
        """Test API documentation endpoints"""
        # Test Swagger UI
        response = client.get("/docs")
        assert response.status_code == 200
        
        # Test OpenAPI spec
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        openapi_data = response.json()
        assert "paths" in openapi_data
        assert "/api/search" in openapi_data["paths"]
        assert "/api/ranking" in openapi_data["paths"]

    @pytest.mark.integration
    def test_health_check_integration(self, client):
        """Test health check endpoint"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "ok"
        assert "SearchFace API is running" in data["message"]