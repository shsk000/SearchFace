"""
Test configuration for pytest
Provides global fixtures and mock configurations for all tests
"""
import pytest
import os
from unittest.mock import patch


@pytest.fixture(autouse=True)
def mock_turso_environment():
    """
    Auto-use fixture to mock Turso environment variables for all tests.
    
    This ensures that tests don't require actual Turso credentials
    and prevents accidental connection to production databases.
    """
    with patch.dict(os.environ, {
        'TURSO_DATABASE_URL': 'libsql://test-database.turso.io',
        'TURSO_AUTH_TOKEN': 'test-auth-token'
    }, clear=False):
        yield


@pytest.fixture(autouse=True)
def mock_data_directory(tmp_path):
    """
    Auto-use fixture to ensure data directory exists for tests.
    
    Creates a temporary data directory structure that mirrors
    the production layout but doesn't interfere with actual data.
    """
    # Create temporary data directory structure
    data_dir = tmp_path / "data"
    data_dir.mkdir(exist_ok=True)
    
    # Create empty database and index files to prevent file not found errors
    (data_dir / "face_database.db").touch()
    (data_dir / "face.index").touch()
    
    # Patch the data paths to use temporary directory
    with patch('src.database.face_database.FaceDatabase.DB_PATH', str(data_dir / "face_database.db")), \
         patch('src.database.face_database.FaceDatabase.INDEX_PATH', str(data_dir / "face.index")), \
         patch('src.database.person_database.PersonDatabase.DB_PATH', str(data_dir / "face_database.db")), \
         patch('src.database.face_index_database.FaceIndexDatabase.DB_PATH', str(data_dir / "face_database.db")), \
         patch('src.database.face_index_database.FaceIndexDatabase.INDEX_PATH', str(data_dir / "face.index")):
        yield data_dir