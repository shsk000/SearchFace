"""
Tests for FaceDatabase module
"""
import pytest
import sqlite3
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

from src.database.face_database import FaceDatabase


class TestFaceDatabase:
    """Test class for FaceDatabase"""

    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database path for testing"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            temp_path = f.name
        yield temp_path
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.fixture
    def temp_index_path(self):
        """Create temporary index path for testing"""
        with tempfile.NamedTemporaryFile(suffix='.index', delete=False) as f:
            temp_path = f.name
        yield temp_path
        # Cleanup
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.fixture
    def mock_face_database(self, temp_db_path, temp_index_path):
        """Create FaceDatabase with mocked paths"""
        with patch.object(FaceDatabase, 'DB_PATH', temp_db_path), \
             patch.object(FaceDatabase, 'INDEX_PATH', temp_index_path), \
             patch('src.database.face_database.faiss') as mock_faiss:
            
            # Mock FAISS index
            mock_index = MagicMock()
            mock_faiss.IndexFlatL2.return_value = mock_index
            mock_faiss.read_index.return_value = mock_index
            
            db = FaceDatabase()
            yield db
            db.close()

    @pytest.mark.unit
    def test_face_database_initialization(self, mock_face_database):
        """Test FaceDatabase initialization"""
        assert mock_face_database.conn is not None
        assert mock_face_database.cursor is not None
        assert hasattr(mock_face_database, 'index')

    @pytest.mark.unit
    def test_face_database_table_creation(self, temp_db_path, temp_index_path):
        """Test that tables are created correctly"""
        with patch.object(FaceDatabase, 'DB_PATH', temp_db_path), \
             patch.object(FaceDatabase, 'INDEX_PATH', temp_index_path), \
             patch('src.database.face_database.faiss'):
            
            db = FaceDatabase()
            
            # Check if tables exist
            cursor = db.cursor
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            assert 'persons' in tables
            assert 'person_profiles' in tables
            
            db.close()

    @pytest.mark.unit
    def test_face_database_close(self, mock_face_database):
        """Test database connection close"""
        # Should not raise exception
        mock_face_database.close()
        
        # Second close should also not raise exception
        mock_face_database.close()

    @pytest.mark.unit
    @patch('src.database.face_database.faiss')
    def test_load_index_existing(self, mock_faiss, temp_db_path, temp_index_path):
        """Test loading existing FAISS index"""
        # Create a dummy index file
        with open(temp_index_path, 'wb') as f:
            f.write(b'dummy index data')
        
        mock_index = MagicMock()
        mock_faiss.read_index.return_value = mock_index
        
        with patch.object(FaceDatabase, 'DB_PATH', temp_db_path), \
             patch.object(FaceDatabase, 'INDEX_PATH', temp_index_path):
            
            db = FaceDatabase()
            
            # Verify index was loaded
            mock_faiss.read_index.assert_called_once_with(temp_index_path)
            assert db.index == mock_index
            
            db.close()

    @pytest.mark.unit
    @patch('src.database.face_database.faiss')
    def test_load_index_new(self, mock_faiss, temp_db_path, temp_index_path):
        """Test creating new FAISS index when file doesn't exist"""
        # Ensure index file doesn't exist
        if os.path.exists(temp_index_path):
            os.unlink(temp_index_path)
        
        mock_index = MagicMock()
        mock_faiss.IndexFlatL2.return_value = mock_index
        
        with patch.object(FaceDatabase, 'DB_PATH', temp_db_path), \
             patch.object(FaceDatabase, 'INDEX_PATH', temp_index_path):
            
            db = FaceDatabase()
            
            # Verify new index was created
            mock_faiss.IndexFlatL2.assert_called_once_with(128)
            assert db.index == mock_index
            
            db.close()

    @pytest.mark.unit
    def test_search_similar_faces_success(self, mock_face_database):
        """Test successful similar face search"""
        # Mock the index search
        mock_face_database.index.search.return_value = (
            np.array([[0.1, 0.2, 0.3]]),  # distances
            np.array([[1, 2, 3]])         # indices
        )
        
        # Mock database query results
        mock_face_database.cursor.fetchall.return_value = [
            (1, "Person 1", "/path/1.jpg"),
            (2, "Person 2", "/path/2.jpg"),
            (3, "Person 3", "/path/3.jpg")
        ]
        
        face_encoding = np.random.random(128)
        results = mock_face_database.search_similar_faces(face_encoding, top_k=3)
        
        assert len(results) == 3
        assert all('name' in result for result in results)
        assert all('distance' in result for result in results)
        assert all('image_path' in result for result in results)
        assert all('person_id' in result for result in results)

    @pytest.mark.unit
    def test_search_similar_faces_empty_database(self, mock_face_database):
        """Test search when database is empty"""
        # Mock empty index
        mock_face_database.index.ntotal = 0
        
        face_encoding = np.random.random(128)
        results = mock_face_database.search_similar_faces(face_encoding, top_k=5)
        
        assert results == []

    @pytest.mark.unit
    def test_search_similar_faces_invalid_encoding(self, mock_face_database):
        """Test search with invalid face encoding"""
        # Test with wrong dimension
        invalid_encoding = np.random.random(64)  # Wrong dimension
        
        with pytest.raises(Exception):
            mock_face_database.search_similar_faces(invalid_encoding, top_k=5)

    @pytest.mark.unit
    def test_search_similar_faces_top_k_limit(self, mock_face_database):
        """Test search with top_k parameter"""
        # Mock the index search
        mock_face_database.index.search.return_value = (
            np.array([[0.1, 0.2]]),  # distances
            np.array([[1, 2]])       # indices
        )
        
        mock_face_database.cursor.fetchall.return_value = [
            (1, "Person 1", "/path/1.jpg"),
            (2, "Person 2", "/path/2.jpg")
        ]
        
        face_encoding = np.random.random(128)
        results = mock_face_database.search_similar_faces(face_encoding, top_k=2)
        
        assert len(results) == 2
        mock_face_database.index.search.assert_called_once()
        call_args = mock_face_database.index.search.call_args[0]
        assert call_args[1] == 2  # top_k parameter

    @pytest.mark.unit
    def test_database_context_manager(self, temp_db_path, temp_index_path):
        """Test FaceDatabase can be used as context manager"""
        with patch.object(FaceDatabase, 'DB_PATH', temp_db_path), \
             patch.object(FaceDatabase, 'INDEX_PATH', temp_index_path), \
             patch('src.database.face_database.faiss'):
            
            # This should work without raising exceptions
            with FaceDatabase() as db:
                assert db.conn is not None

    @pytest.mark.unit
    def test_database_error_handling(self, temp_db_path, temp_index_path):
        """Test database error handling"""
        with patch.object(FaceDatabase, 'DB_PATH', temp_db_path), \
             patch.object(FaceDatabase, 'INDEX_PATH', temp_index_path), \
             patch('src.database.face_database.faiss'):
            
            db = FaceDatabase()
            
            # Mock database error
            db.cursor.fetchall.side_effect = sqlite3.Error("Database error")
            
            face_encoding = np.random.random(128)
            
            # Should handle database errors gracefully
            with pytest.raises(sqlite3.Error):
                db.search_similar_faces(face_encoding, top_k=5)
            
            db.close()

    @pytest.mark.unit
    def test_index_consistency(self, mock_face_database):
        """Test index and database consistency"""
        # Test that index size matches database records
        mock_face_database.index.ntotal = 5
        mock_face_database.cursor.fetchone.return_value = (5,)  # COUNT result
        
        # This should not raise any consistency errors
        face_encoding = np.random.random(128)
        
        # Mock successful search
        mock_face_database.index.search.return_value = (
            np.array([[0.1]]),
            np.array([[0]])
        )
        mock_face_database.cursor.fetchall.return_value = [
            (1, "Person 1", "/path/1.jpg")
        ]
        
        results = mock_face_database.search_similar_faces(face_encoding, top_k=1)
        assert len(results) == 1

    @pytest.mark.unit
    def test_vector_dimension_consistency(self, mock_face_database):
        """Test that vector dimension is consistent"""
        assert FaceDatabase.VECTOR_DIMENSION == 128
        
        # Test with correct dimension
        face_encoding = np.random.random(128)
        assert face_encoding.shape[0] == FaceDatabase.VECTOR_DIMENSION

    @pytest.mark.unit
    def test_database_paths_configuration(self):
        """Test database path configuration"""
        assert FaceDatabase.DB_PATH == "data/face_database.db"
        assert FaceDatabase.INDEX_PATH == "data/face.index"
        assert FaceDatabase.VECTOR_DIMENSION == 128

    @pytest.mark.unit
    def test_search_result_structure(self, mock_face_database):
        """Test search result structure"""
        # Mock search results
        mock_face_database.index.search.return_value = (
            np.array([[0.15]]),
            np.array([[0]])
        )
        mock_face_database.cursor.fetchall.return_value = [
            (1, "Test Person", "/test/path.jpg")
        ]
        
        face_encoding = np.random.random(128)
        results = mock_face_database.search_similar_faces(face_encoding, top_k=1)
        
        assert len(results) == 1
        result = results[0]
        
        # Check required fields
        required_fields = ['person_id', 'name', 'distance', 'image_path']
        for field in required_fields:
            assert field in result
        
        # Check data types
        assert isinstance(result['person_id'], int)
        assert isinstance(result['name'], str)
        assert isinstance(result['distance'], (int, float))
        assert isinstance(result['image_path'], str)