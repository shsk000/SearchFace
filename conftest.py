"""
Pytest configuration and shared fixtures
"""
import os
import sys
import asyncio
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

# Add the src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))


# Remove custom event_loop fixture to use pytest-asyncio default


@pytest.fixture
def mock_face_database():
    """Mock FaceDatabase for testing"""
    with patch('database.face_database.FaceDatabase') as mock_db:
        mock_instance = MagicMock()
        mock_db.return_value = mock_instance
        
        # Mock search results
        mock_instance.search_similar_faces.return_value = [
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
        
        yield mock_instance


@pytest.fixture
def mock_search_database():
    """Mock SearchDatabase for testing"""
    with patch('database.search_database.SearchDatabase') as mock_db:
        mock_instance = MagicMock()
        mock_db.return_value = mock_instance
        
        # Mock session creation
        mock_instance.record_search_results.return_value = "test-session-123"
        
        # Mock session retrieval
        mock_instance.get_search_session_results.return_value = {
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
        
        yield mock_instance


@pytest.fixture
def mock_ranking_database():
    """Mock RankingDatabase for testing"""
    with patch('database.ranking_database.RankingDatabase') as mock_db:
        mock_instance = MagicMock()
        mock_db.return_value = mock_instance
        
        # Mock ranking data
        mock_instance.get_top_ranking.return_value = [
            {
                'rank': 1,
                'person_id': 1,
                'name': 'Test Person 1',
                'win_count': 10,
                'search_count': 20,
                'win_rate': 0.5
            }
        ]
        
        yield mock_instance


@pytest.fixture
def mock_face_utils():
    """Mock face_utils for testing"""
    with patch('face.face_utils.get_face_encoding_from_array') as mock_func:
        # Return a mock face encoding (128-dimensional vector)
        import numpy as np
        mock_func.return_value = np.random.random(128)
        yield mock_func


@pytest.fixture
def sample_image_file():
    """Create a sample image file for testing"""
    from io import BytesIO
    from PIL import Image
    
    # Create a small test image
    img = Image.new('RGB', (100, 100), color='red')
    img_bytes = BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    return img_bytes


@pytest.fixture
def fastapi_test_client():
    """Create a test client for the FastAPI app"""
    from src.api.main import app
    return TestClient(app)


@pytest.fixture(autouse=True)
def mock_environment():
    """Mock environment variables for testing"""
    with patch.dict(os.environ, {
        'TURSO_DATABASE_URL': 'libsql://test.turso.io',
        'TURSO_AUTH_TOKEN': 'test-token',
        'DEBUG': 'true'
    }):
        yield


@pytest.fixture
def mock_logger():
    """Mock logger for testing"""
    with patch('logging.getLogger') as mock_logger:
        yield mock_logger.return_value