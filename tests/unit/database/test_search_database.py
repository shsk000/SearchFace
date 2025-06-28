"""
Tests for SearchDatabase module
"""
import pytest
import uuid
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

from src.database.search_database import SearchDatabase


class TestSearchDatabase:
    """Test class for SearchDatabase"""

    @pytest.fixture
    def mock_libsql_connection(self):
        """Mock libsql connection"""
        with patch('src.database.search_database.libsql') as mock_libsql:
            mock_conn = MagicMock()
            mock_libsql.connect.return_value = mock_conn
            yield mock_conn

    @pytest.fixture
    def mock_search_database(self, mock_libsql_connection):
        """Create SearchDatabase with mocked connection"""
        with patch.dict(os.environ, {
            'TURSO_DATABASE_URL': 'libsql://test.turso.io',
            'TURSO_AUTH_TOKEN': 'test-token'
        }, clear=False):
            db = SearchDatabase()
            yield db

    @pytest.mark.unit
    def test_search_database_initialization_success(self, mock_libsql_connection):
        """Test successful SearchDatabase initialization"""
        with patch.dict(os.environ, {
            'TURSO_DATABASE_URL': 'libsql://test.turso.io',
            'TURSO_AUTH_TOKEN': 'test-token'
        }, clear=False):
            db = SearchDatabase()
            
            assert db.db_url == 'libsql://test.turso.io'
            assert db.db_token == 'test-token'
            assert db.conn == mock_libsql_connection

    @pytest.mark.unit
    def test_search_database_initialization_missing_url(self):
        """Test SearchDatabase initialization with missing URL"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="TURSO_DATABASE_URL環境変数が設定されていません"):
                SearchDatabase()

    @pytest.mark.unit
    def test_search_database_initialization_missing_token(self, mock_libsql_connection):
        """Test SearchDatabase initialization with missing token"""
        with patch.dict(os.environ, {
            'TURSO_DATABASE_URL': 'libsql://test.turso.io'
        }, clear=True):
            # Should still work, token is optional for some operations
            db = SearchDatabase()
            assert db.db_token is None

    @pytest.mark.unit
    def test_record_search_results_success(self, mock_search_database):
        """Test successful search results recording"""
        search_results = [
            {
                'person_id': 1,
                'name': 'Person 1',
                'distance': 0.1,
                'image_path': '/path/1.jpg'
            },
            {
                'person_id': 2,
                'name': 'Person 2',
                'distance': 0.2,
                'image_path': '/path/2.jpg'
            }
        ]
        metadata = {'filename': 'test.jpg', 'file_size': 1024}
        
        # Mock UUID generation
        with patch('src.database.search_database.uuid.uuid4') as mock_uuid:
            mock_uuid.return_value = Mock()
            mock_uuid.return_value.__str__ = Mock(return_value='test-session-123')
            
            session_id = mock_search_database.record_search_results(search_results, metadata)
            
            assert session_id == 'test-session-123'
            
            # Verify database calls
            assert mock_search_database.conn.execute.call_count >= 2  # At least 2 inserts
            mock_search_database.conn.commit.assert_called_once()

    @pytest.mark.unit
    def test_record_search_results_empty_list(self, mock_search_database):
        """Test recording empty search results"""
        search_results = []
        
        with patch('src.database.search_database.uuid.uuid4') as mock_uuid:
            mock_uuid.return_value = Mock()
            mock_uuid.return_value.__str__ = Mock(return_value='empty-session-123')
            
            session_id = mock_search_database.record_search_results(search_results)
            
            assert session_id == 'empty-session-123'
            # No insert calls should be made for empty results
            # But commit and sync should still be called
            mock_search_database.conn.execute.assert_not_called()
            mock_search_database.conn.commit.assert_called_once()
            assert mock_search_database.conn.sync.call_count >= 1  # Called in __init__ and record_search_results

    @pytest.mark.unit
    def test_record_search_results_limit_five(self, mock_search_database):
        """Test that only top 5 results are recorded"""
        search_results = [
            {'person_id': i, 'name': f'Person {i}', 'distance': 0.1 * i, 'image_path': f'/path/{i}.jpg'}
            for i in range(1, 8)  # 7 results
        ]
        
        with patch('src.database.search_database.uuid.uuid4') as mock_uuid:
            mock_uuid.return_value = Mock()
            mock_uuid.return_value.__str__ = Mock(return_value='limited-session-123')
            
            session_id = mock_search_database.record_search_results(search_results)
            
            assert session_id == 'limited-session-123'
            # Should only make 5 insert calls (for top 5 results)
            assert mock_search_database.conn.execute.call_count == 5

    @pytest.mark.unit
    def test_record_search_results_with_metadata(self, mock_search_database):
        """Test recording search results with metadata"""
        search_results = [
            {
                'person_id': 1,
                'name': 'Person 1',
                'distance': 0.1,
                'image_path': '/path/1.jpg'
            }
        ]
        metadata = {
            'filename': 'test.jpg',
            'file_size': 2048,
            'processing_time': 0.45
        }
        
        session_id = mock_search_database.record_search_results(search_results, metadata)
        
        assert session_id is not None
        # Verify metadata was passed to database
        mock_search_database.conn.execute.assert_called()

    @pytest.mark.unit
    def test_record_search_results_database_error(self, mock_search_database):
        """Test record_search_results with database error"""
        search_results = [
            {
                'person_id': 1,
                'name': 'Person 1',
                'distance': 0.1,
                'image_path': '/path/1.jpg'
            }
        ]
        
        # Mock database error
        mock_search_database.conn.execute.side_effect = Exception("Database error")
        
        with pytest.raises(Exception, match="Database error"):
            mock_search_database.record_search_results(search_results)

    @pytest.mark.unit
    def test_get_search_session_results_success(self, mock_search_database):
        """Test successful search session results retrieval"""
        session_id = 'test-session-123'
        
        # Mock the first query for session info
        mock_session_result = MagicMock()
        mock_session_result.fetchall.return_value = [
            ('2024-01-01 10:00:00', '{"filename": "test.jpg"}')  # search_timestamp, metadata
        ]
        
        # Mock the second query for results
        mock_results_query = MagicMock()
        mock_results_query.fetchall.return_value = [
            (1, 1, 0.1, '/path/1.jpg')  # result_rank, person_id, distance, image_path
        ]
        
        mock_search_database.conn.execute.side_effect = [mock_session_result, mock_results_query]
        
        # Mock the local SQLite connection for person name lookup
        with patch('sqlite3.connect') as mock_sqlite_connect:
            mock_local_conn = MagicMock()
            mock_local_cursor = MagicMock()
            mock_local_cursor.fetchall.return_value = [(1, 'Person 1')]
            mock_local_conn.cursor.return_value = mock_local_cursor
            mock_sqlite_connect.return_value = mock_local_conn
            
            result = mock_search_database.get_search_session_results(session_id)
        
        assert result is not None
        assert result['session_id'] == session_id
        assert 'search_timestamp' in result
        assert 'metadata' in result
        assert 'results' in result

    @pytest.mark.unit
    def test_get_search_session_results_not_found(self, mock_search_database):
        """Test search session results retrieval when session not found"""
        session_id = 'non-existent-session'
        
        # Mock empty query result
        mock_session_result = MagicMock()
        mock_session_result.fetchall.return_value = []
        mock_search_database.conn.execute.return_value = mock_session_result
        
        result = mock_search_database.get_search_session_results(session_id)
        
        assert result is None

    @pytest.mark.unit
    def test_get_search_session_results_database_error(self, mock_search_database):
        """Test get_search_session_results with database error"""
        session_id = 'test-session-123'
        
        # Mock database error
        mock_search_database.conn.execute.side_effect = Exception("Database error")
        
        with pytest.raises(Exception, match="Database error"):
            mock_search_database.get_search_session_results(session_id)

    @pytest.mark.unit
    def test_get_search_stats_success(self, mock_search_database):
        """Test successful search statistics retrieval"""
        # Mock statistics query results for multiple calls
        mock_result1 = MagicMock()
        mock_result1.fetchall.return_value = [(100,)]  # total_search_sessions
        
        mock_result2 = MagicMock()
        mock_result2.fetchall.return_value = [(250,)]  # total_search_results
        
        mock_result3 = MagicMock()
        mock_result3.fetchall.return_value = [('2024-01-01 10:00:00',)]  # first_search
        
        mock_result4 = MagicMock()
        mock_result4.fetchall.return_value = [('2024-01-01 15:00:00',)]  # latest_search
        
        mock_search_database.conn.execute.side_effect = [mock_result1, mock_result2, mock_result3, mock_result4]
        
        stats = mock_search_database.get_search_stats()
        
        assert isinstance(stats, dict)
        assert 'total_search_sessions' in stats
        assert 'total_search_results' in stats
        assert 'first_search_date' in stats
        assert 'latest_search_date' in stats

    @pytest.mark.unit
    def test_get_search_stats_database_error(self, mock_search_database):
        """Test get_search_stats with database error"""
        # Mock database error
        mock_search_database.conn.execute.side_effect = Exception("Database error")
        
        with pytest.raises(Exception, match="Database error"):
            mock_search_database.get_search_stats()

    @pytest.mark.unit
    def test_get_search_history_success(self, mock_search_database):
        """Test successful search history retrieval"""
        # Mock history query result
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            (1, 'session-1', 1, 1, 0.1, '/path/1.jpg', '2024-01-01 10:00:00', None),  # history_id, search_session_id, result_rank, person_id, distance, image_path, search_timestamp, metadata
            (2, 'session-2', 1, 2, 0.2, '/path/2.jpg', '2024-01-01 11:00:00', None)
        ]
        mock_search_database.conn.execute.return_value = mock_result
        
        # Mock the local SQLite connection for person name lookup
        with patch('sqlite3.connect') as mock_sqlite_connect:
            mock_local_conn = MagicMock()
            mock_local_cursor = MagicMock()
            mock_local_cursor.fetchall.return_value = [(1, 'Person 1'), (2, 'Person 2')]
            mock_local_conn.cursor.return_value = mock_local_cursor
            mock_sqlite_connect.return_value = mock_local_conn
            
            history = mock_search_database.get_search_history(limit=10, person_id=1)
        
        assert isinstance(history, list)
        assert len(history) == 2

    @pytest.mark.unit
    def test_get_search_sessions_success(self, mock_search_database):
        """Test successful search sessions retrieval"""
        # Mock the main sessions query
        mock_sessions_result = MagicMock()
        mock_sessions_result.fetchall.return_value = [
            ('session-1', '2024-01-01 10:00:00', 2),  # search_session_id, search_timestamp, result_count
            ('session-2', '2024-01-01 11:00:00', 1)
        ]
        
        # Mock the detail queries for each session
        mock_detail_result1 = MagicMock()
        mock_detail_result1.fetchall.return_value = [
            (1, 1, 0.1, '/path/1.jpg'),  # result_rank, person_id, distance, image_path
            (2, 2, 0.2, '/path/2.jpg')
        ]
        
        mock_detail_result2 = MagicMock()
        mock_detail_result2.fetchall.return_value = [
            (1, 3, 0.15, '/path/3.jpg')
        ]
        
        mock_search_database.conn.execute.side_effect = [mock_sessions_result, mock_detail_result1, mock_detail_result2]
        
        # Mock the local SQLite connection for person name lookup
        with patch('sqlite3.connect') as mock_sqlite_connect:
            mock_local_conn = MagicMock()
            mock_local_cursor = MagicMock()
            mock_local_cursor.fetchall.side_effect = [
                [(1, 'Person 1'), (2, 'Person 2')],  # For session-1
                [(3, 'Person 3')]  # For session-2
            ]
            mock_local_conn.cursor.return_value = mock_local_cursor
            mock_sqlite_connect.return_value = mock_local_conn
            
            sessions = mock_search_database.get_search_sessions(limit=50)
        
        assert isinstance(sessions, list)
        assert len(sessions) == 2

    @pytest.mark.unit
    def test_close_connection(self, mock_search_database):
        """Test database connection close"""
        # Should not raise exception (close is a no-op in libsql implementation)
        mock_search_database.close()
        
        # Second close should also not raise exception
        mock_search_database.close()

    @pytest.mark.unit
    def test_sync_database(self, mock_search_database):
        """Test database synchronization"""
        # Should work without errors
        mock_search_database.conn.sync.assert_called_once()

    @pytest.mark.unit
    def test_session_id_generation(self, mock_search_database):
        """Test that session IDs are properly generated"""
        search_results = [
            {
                'person_id': 1,
                'name': 'Person 1',
                'distance': 0.1,
                'image_path': '/path/1.jpg'
            }
        ]
        
        session_id1 = mock_search_database.record_search_results(search_results)
        session_id2 = mock_search_database.record_search_results(search_results)
        
        # Session IDs should be different (UUID4 generates unique IDs)
        assert session_id1 != session_id2
        assert isinstance(session_id1, str)
        assert isinstance(session_id2, str)

    @pytest.mark.unit
    def test_metadata_json_handling(self, mock_search_database):
        """Test that metadata is properly handled as JSON"""
        search_results = [
            {
                'person_id': 1,
                'name': 'Person 1',
                'distance': 0.1,
                'image_path': '/path/1.jpg'
            }
        ]
        
        # Test with complex metadata
        metadata = {
            'filename': 'test.jpg',
            'file_size': 1024,
            'nested': {
                'key': 'value',
                'number': 42
            }
        }
        
        session_id = mock_search_database.record_search_results(search_results, metadata)
        
        assert session_id is not None
        # Verify that execute was called (metadata would be JSON-encoded)
        mock_search_database.conn.execute.assert_called()

    @pytest.mark.unit
    def test_result_ranking_order(self, mock_search_database):
        """Test that results are recorded with correct ranking order"""
        search_results = [
            {'person_id': 1, 'name': 'First', 'distance': 0.1, 'image_path': '/path/1.jpg'},
            {'person_id': 2, 'name': 'Second', 'distance': 0.2, 'image_path': '/path/2.jpg'},
            {'person_id': 3, 'name': 'Third', 'distance': 0.3, 'image_path': '/path/3.jpg'}
        ]
        
        session_id = mock_search_database.record_search_results(search_results)
        
        assert session_id is not None
        # Verify that execute was called 3 times (for 3 results)
        assert mock_search_database.conn.execute.call_count == 3