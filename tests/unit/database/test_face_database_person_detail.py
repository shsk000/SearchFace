"""
Tests for FaceDatabase get_person_detail method with dict-style column access
"""
import pytest
import sqlite3
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

from src.database.face_database import FaceDatabase
from tests.utils.database_test_utils import isolated_test_database, create_test_person_data


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
             patch('src.database.face_index_database.faiss') as mock_faiss, \
             patch('src.database.face_index_database.FaceIndexDatabase._verify_tables_exist'):
            
            # Mock FAISS index
            mock_index = MagicMock()
            mock_faiss.IndexFlatL2.return_value = mock_index
            mock_faiss.read_index.return_value = mock_index
            
            db = FaceDatabase()
            
            # Mock PersonDatabase for testing since FaceDatabase delegates to it
            db.person_db = MagicMock()
            
            yield db
            db.close()

    @pytest.mark.unit
    def test_get_person_detail_success_with_dict_access(self, mock_face_database):
        """Test get_person_detail method with dict-style column access"""
        # Mock the expected return data
        expected_result = {
            'person_id': 1,
            'name': 'Test Person',
            'base_image_path': '/path/to/base/image.jpg'
        }
        
        # Mock PersonDatabase.get_person_detail directly since FaceDatabase delegates to it
        mock_face_database.person_db.get_person_detail.return_value = expected_result
        
        # Test the method
        result = mock_face_database.get_person_detail(1)
        
        # Verify the result
        assert result is not None
        assert result['person_id'] == 1
        assert result['name'] == 'Test Person'
        assert result['base_image_path'] == '/path/to/base/image.jpg'
        
        # Verify PersonDatabase.get_person_detail was called correctly
        mock_face_database.person_db.get_person_detail.assert_called_once_with(1)

    @pytest.mark.unit
    def test_get_person_detail_not_found_with_dict_access(self, mock_face_database):
        """Test get_person_detail method when person is not found"""
        # Mock PersonDatabase.get_person_detail to return None
        mock_face_database.person_db.get_person_detail.return_value = None
        
        # Test the method
        result = mock_face_database.get_person_detail(999)
        
        # Verify the result
        assert result is None
        
        # Verify PersonDatabase.get_person_detail was called correctly
        mock_face_database.person_db.get_person_detail.assert_called_once_with(999)

    @pytest.mark.unit
    def test_get_person_detail_with_none_image_path_dict_access(self, mock_face_database):
        """Test get_person_detail method when base_image_path is None"""
        # Mock the expected return data with None image path
        expected_result = {
            'person_id': 2,
            'name': 'Person Without Image',
            'base_image_path': None
        }
        
        # Mock PersonDatabase.get_person_detail to return expected result
        mock_face_database.person_db.get_person_detail.return_value = expected_result
        
        # Test the method
        result = mock_face_database.get_person_detail(2)
        
        # Verify the result
        assert result is not None
        assert result['person_id'] == 2
        assert result['name'] == 'Person Without Image'
        assert result['base_image_path'] is None
        
        # Verify PersonDatabase.get_person_detail was called correctly
        mock_face_database.person_db.get_person_detail.assert_called_once_with(2)

    @pytest.mark.unit  
    def test_row_factory_enabled_in_init(self, temp_db_path, temp_index_path):
        """Test that sqlite3.Row factory is properly set during initialization"""
        with patch.object(FaceDatabase, 'DB_PATH', temp_db_path), \
             patch.object(FaceDatabase, 'INDEX_PATH', temp_index_path), \
             patch('src.database.face_index_database.faiss'), \
             patch('src.database.face_index_database.FaceIndexDatabase._verify_tables_exist'):
            
            db = FaceDatabase()
            
            # Verify row factory is set to sqlite3.Row
            assert db.conn.row_factory == sqlite3.Row
            
            db.close()

    @pytest.mark.unit
    def test_get_person_detail_integration_with_real_row_factory(self, temp_db_path, temp_index_path):
        """Integration test with real sqlite3.Row to verify dict-style access works"""
        # CRITICAL: Mock PersonDatabase to prevent production DB access
        with patch.object(FaceDatabase, 'DB_PATH', temp_db_path), \
             patch.object(FaceDatabase, 'INDEX_PATH', temp_index_path), \
             patch('src.database.face_index_database.faiss'), \
             patch('src.database.face_index_database.FaceIndexDatabase._verify_tables_exist'), \
             patch('src.database.person_database.PersonDatabase._create_tables'):
            
            # Use test utility for safe database creation with proper schema
            with isolated_test_database() as (test_conn, test_db_path):
                # Create test person data using utility function
                person_id = create_test_person_data(
                    test_conn, 
                    person_name='Integration Test Person',
                    base_image_path='/tmp/integration_test_path.jpg'  # SAFE: tmp path
                )
                
                # Create FaceDatabase and replace its connection with test connection
                db = FaceDatabase()
                db.person_db.conn = test_conn
                db.person_db.cursor = test_conn.cursor()
                
                # Test the method with real data
                result = db.get_person_detail(person_id)
                
                # Verify the result
                assert result is not None
                assert result['person_id'] == person_id
                assert result['name'] == 'Integration Test Person'
                assert result['base_image_path'] == '/tmp/integration_test_path.jpg'
                
                # Test with non-existent person
                result_none = db.get_person_detail(999)
                assert result_none is None
                
                # FaceDatabase cleanup (test_conn auto-closed by context manager)
                db.close()