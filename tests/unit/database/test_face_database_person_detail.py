"""
Tests for FaceDatabase get_person_detail method with dict-style column access
"""
import pytest
import sqlite3
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

from src.database.face_database import FaceDatabase


class TestFaceDatabasePersonDetail:
    """Test class for FaceDatabase get_person_detail method"""

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
        """Create FaceDatabase with mocked paths and row factory enabled"""
        with patch.object(FaceDatabase, 'DB_PATH', temp_db_path), \
             patch.object(FaceDatabase, 'INDEX_PATH', temp_index_path), \
             patch('src.database.face_database.faiss') as mock_faiss:
            
            # Mock FAISS index
            mock_index = MagicMock()
            mock_faiss.IndexFlatL2.return_value = mock_index
            mock_faiss.read_index.return_value = mock_index
            
            db = FaceDatabase()
            
            # Mock the cursor for testing
            db.cursor = MagicMock()
            
            yield db
            db.close()

    @pytest.mark.unit
    def test_get_person_detail_success_with_dict_access(self, mock_face_database):
        """Test get_person_detail method with dict-style column access"""
        # Create a sqlite3.Row-like mock object
        mock_row = MagicMock()
        mock_row.__getitem__.side_effect = lambda key: {
            'person_id': 1,
            'name': 'Test Person',
            'base_image_path': '/path/to/base/image.jpg'
        }[key]
        
        # Mock the cursor fetchone to return our mock row
        mock_face_database.cursor.fetchone.return_value = mock_row
        
        # Test the method
        result = mock_face_database.get_person_detail(1)
        
        # Verify the result
        assert result is not None
        assert result['person_id'] == 1
        assert result['name'] == 'Test Person'
        assert result['image_path'] == '/path/to/base/image.jpg'
        
        # Verify the SQL query was executed correctly
        mock_face_database.cursor.execute.assert_called_once()
        sql_call = mock_face_database.cursor.execute.call_args[0][0]
        assert 'SELECT p.person_id, p.name, pp.base_image_path' in sql_call
        assert 'WHERE p.person_id = ?' in sql_call

    @pytest.mark.unit
    def test_get_person_detail_not_found_with_dict_access(self, mock_face_database):
        """Test get_person_detail method when person is not found"""
        # Mock the cursor fetchone to return None
        mock_face_database.cursor.fetchone.return_value = None
        
        # Test the method
        result = mock_face_database.get_person_detail(999)
        
        # Verify the result
        assert result is None
        
        # Verify the SQL query was executed correctly
        mock_face_database.cursor.execute.assert_called_once_with(
            """
            SELECT p.person_id, p.name, pp.base_image_path
            FROM persons p
            LEFT JOIN person_profiles pp ON p.person_id = pp.person_id
            WHERE p.person_id = ?
        """, (999,))

    @pytest.mark.unit
    def test_get_person_detail_with_none_image_path_dict_access(self, mock_face_database):
        """Test get_person_detail method when base_image_path is None"""
        # Create a sqlite3.Row-like mock object with None image path
        mock_row = MagicMock()
        mock_row.__getitem__.side_effect = lambda key: {
            'person_id': 2,
            'name': 'Person Without Image',
            'base_image_path': None
        }[key]
        
        # Mock the cursor fetchone to return our mock row
        mock_face_database.cursor.fetchone.return_value = mock_row
        
        # Test the method
        result = mock_face_database.get_person_detail(2)
        
        # Verify the result
        assert result is not None
        assert result['person_id'] == 2
        assert result['name'] == 'Person Without Image'
        assert result['image_path'] is None

    @pytest.mark.unit  
    def test_row_factory_enabled_in_init(self, temp_db_path, temp_index_path):
        """Test that sqlite3.Row factory is properly set during initialization"""
        with patch.object(FaceDatabase, 'DB_PATH', temp_db_path), \
             patch.object(FaceDatabase, 'INDEX_PATH', temp_index_path), \
             patch('src.database.face_database.faiss'):
            
            db = FaceDatabase()
            
            # Verify row factory is set to sqlite3.Row
            assert db.conn.row_factory == sqlite3.Row
            
            db.close()

    @pytest.mark.unit
    def test_get_person_detail_integration_with_real_row_factory(self, temp_db_path, temp_index_path):
        """Integration test with real sqlite3.Row to verify dict-style access works"""
        with patch.object(FaceDatabase, 'DB_PATH', temp_db_path), \
             patch.object(FaceDatabase, 'INDEX_PATH', temp_index_path), \
             patch('src.database.face_database.faiss'):
            
            db = FaceDatabase()
            
            # Insert test data directly into the database
            db.cursor.execute(
                "INSERT INTO persons (person_id, name) VALUES (?, ?)",
                (1, 'Integration Test Person')
            )
            db.cursor.execute(
                "INSERT INTO person_profiles (person_id, base_image_path) VALUES (?, ?)",
                (1, '/integration/test/path.jpg')
            )
            db.conn.commit()
            
            # Test the method with real data
            result = db.get_person_detail(1)
            
            # Verify the result
            assert result is not None
            assert result['person_id'] == 1
            assert result['name'] == 'Integration Test Person'
            assert result['image_path'] == '/integration/test/path.jpg'
            
            # Test with non-existent person
            result_none = db.get_person_detail(999)
            assert result_none is None
            
            db.close()