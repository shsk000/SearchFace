"""
Tests for API main module
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from src.api.main import app


class TestMainApp:
    """Test class for main FastAPI application"""

    @pytest.fixture
    def client(self):
        """Test client fixture"""
        return TestClient(app)

    @pytest.mark.unit
    def test_app_initialization(self):
        """Test that FastAPI app is properly initialized"""
        assert app.title == "SearchFace API"
        assert app.description == "顔画像の類似検索API"
        assert app.version == "1.0.0"

    @pytest.mark.unit
    def test_root_endpoint(self, client):
        """Test root health check endpoint"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "ok"
        assert data["message"] == "SearchFace API is running"

    @pytest.mark.unit
    def test_cors_configuration(self):
        """Test CORS middleware configuration"""
        # Check that CORS middleware is configured
        middlewares = [middleware.cls.__name__ for middleware in app.user_middleware]
        assert "CORSMiddleware" in middlewares

    @pytest.mark.unit
    def test_middleware_configuration(self):
        """Test that error handling middleware is configured"""
        # Check that custom middleware is configured
        assert len(app.user_middleware) > 0

    @pytest.mark.unit
    def test_router_inclusion(self):
        """Test that API routers are properly included"""
        # Check that routes are included
        routes = [route.path for route in app.routes]
        
        # Should have API routes
        api_routes = [route for route in routes if route.startswith("/api")]
        assert len(api_routes) > 0

    @pytest.mark.unit
    def test_search_routes_included(self, client):
        """Test that search routes are accessible"""
        # Test that search endpoints exist (should get method not allowed for GET)
        response = client.get("/api/search")
        # Should be 405 (Method Not Allowed) or 422 (for POST with missing data)
        assert response.status_code in [405, 422]

    @pytest.mark.unit
    def test_ranking_routes_included(self, client):
        """Test that ranking routes are accessible"""
        # Mock the database and sync check to avoid actual DB calls
        with patch('src.api.routes.ranking.is_sync_complete', return_value=True), \
             patch('src.api.routes.ranking.RankingDatabase') as mock_db:
            mock_db_instance = mock_db.return_value
            mock_db_instance.get_ranking.return_value = []
            
            response = client.get("/api/ranking")
            assert response.status_code == 200

    @pytest.mark.unit
    def test_start_function(self):
        """Test the start function exists and is callable"""
        from src.api.main import start
        
        assert callable(start)
        
        # Test with mock uvicorn
        with patch('src.api.main.uvicorn.run') as mock_run:
            start(host="127.0.0.1", port=8080)
            mock_run.assert_called_once_with(app, host="127.0.0.1", port=8080)

    @pytest.mark.unit
    def test_start_function_defaults(self):
        """Test start function with default parameters"""
        from src.api.main import start
        
        with patch('src.api.main.uvicorn.run') as mock_run:
            start()
            mock_run.assert_called_once_with(app, host="0.0.0.0", port=10000)

    @pytest.mark.unit
    def test_app_metadata(self):
        """Test application metadata is properly set"""
        assert hasattr(app, 'title')
        assert hasattr(app, 'description')
        assert hasattr(app, 'version')
        
        assert isinstance(app.title, str)
        assert isinstance(app.description, str)
        assert isinstance(app.version, str)

    @pytest.mark.unit
    def test_openapi_documentation(self, client):
        """Test that OpenAPI documentation is available"""
        response = client.get("/docs")
        assert response.status_code == 200
        
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        # Check that OpenAPI spec contains our API info
        openapi_data = response.json()
        assert openapi_data["info"]["title"] == "SearchFace API"