"""
Tests for ranking API routes
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from src.api.main import app


class TestRankingRoutes:
    """Test class for ranking route endpoints"""

    @pytest.fixture
    def client(self):
        """Test client fixture"""
        return TestClient(app)

    @pytest.mark.unit
    @patch('src.api.routes.ranking.is_sync_complete', return_value=True)
    @patch('src.api.routes.ranking.RankingDatabase')
    def test_get_ranking_success(self, mock_ranking_db, mock_sync_complete, client):
        """Test successful ranking retrieval"""
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
                'last_win_date': '2023-01-01T00:00:00',
                'image_path': '/test/image1.jpg'
            },
            {
                'rank': 2,
                'person_id': 2,
                'name': 'Test Person 2',
                'win_count': 8,
                'search_count': 15,
                'win_rate': 0.53,
                'last_win_date': '2023-01-02T00:00:00',
                'image_path': '/test/image2.jpg'
            }
        ]
        mock_ranking_db_instance.get_ranking.return_value = mock_ranking_data
        
        response = client.get("/api/ranking")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "ranking" in data
        assert "total_count" in data
        assert data["total_count"] == 2
        assert len(data["ranking"]) == 2
        
        # Check first ranking item
        first_item = data["ranking"][0]
        assert first_item["rank"] == 1
        assert first_item["person_id"] == 1
        assert first_item["name"] == "Test Person 1"
        assert first_item["win_count"] == 10
        
        # Verify database call
        mock_ranking_db_instance.get_ranking.assert_called_once_with(limit=10)

    @pytest.mark.unit
    @patch('src.api.routes.ranking.is_sync_complete', return_value=True)
    @patch('src.api.routes.ranking.RankingDatabase')
    def test_get_ranking_with_limit(self, mock_ranking_db, mock_sync_complete, client):
        """Test ranking retrieval with custom limit"""
        mock_ranking_db_instance = MagicMock()
        mock_ranking_db.return_value = mock_ranking_db_instance
        mock_ranking_db_instance.get_ranking.return_value = []
        
        response = client.get("/api/ranking?limit=5")
        
        assert response.status_code == 200
        # Verify that limit parameter was passed correctly
        mock_ranking_db_instance.get_ranking.assert_called_once_with(limit=5)

    @pytest.mark.unit
    @patch('src.api.routes.ranking.is_sync_complete', return_value=True)
    @patch('src.api.routes.ranking.RankingDatabase')
    def test_get_ranking_limit_max_constraint(self, mock_ranking_db, mock_sync_complete, client):
        """Test that ranking limit is constrained to maximum of 10"""
        mock_ranking_db_instance = MagicMock()
        mock_ranking_db.return_value = mock_ranking_db_instance
        mock_ranking_db_instance.get_ranking.return_value = []
        
        # Request with limit higher than maximum
        response = client.get("/api/ranking?limit=20")
        
        assert response.status_code == 200
        # Verify that limit was capped at 10
        mock_ranking_db_instance.get_ranking.assert_called_once_with(limit=10)

    @pytest.mark.unit
    @patch('src.api.routes.ranking.is_sync_complete', return_value=True)
    @patch('src.api.routes.ranking.RankingDatabase')
    def test_get_ranking_database_error(self, mock_ranking_db, mock_sync_complete, client):
        """Test ranking retrieval when database error occurs"""
        mock_ranking_db_instance = MagicMock()
        mock_ranking_db.return_value = mock_ranking_db_instance
        mock_ranking_db_instance.get_ranking.side_effect = Exception("Database error")
        
        response = client.get("/api/ranking")
        
        assert response.status_code == 500

    @pytest.mark.unit
    @patch('src.api.routes.ranking.is_sync_complete', return_value=True)
    @patch('src.api.routes.ranking.SearchDatabase')
    @patch('src.api.routes.ranking.RankingDatabase')
    def test_get_ranking_stats_success(self, mock_ranking_db, mock_search_db, mock_sync_complete, client):
        """Test successful ranking stats retrieval"""
        # Mock ranking database
        mock_ranking_db_instance = MagicMock()
        mock_ranking_db.return_value = mock_ranking_db_instance
        mock_ranking_stats = {
            'total_persons': 100,
            'total_wins': 500,
            'avg_win_rate': 0.25,
            'top_person': {
                'name': 'Top Person',
                'win_count': 50,
                'image_path': '/test/top.jpg'
            }
        }
        mock_ranking_db_instance.get_ranking_stats.return_value = mock_ranking_stats
        
        # Mock search database
        mock_search_db_instance = MagicMock()
        mock_search_db.return_value = mock_search_db_instance
        mock_search_stats = {
            'total_searches': 2000,
            'daily_searches': 50,
            'avg_processing_time': 0.45,
            'total_search_sessions': 1500,
            'total_search_results': 8000,
            'first_search_date': '2023-01-01T00:00:00',
            'latest_search_date': '2023-12-31T23:59:59'
        }
        mock_search_db_instance.get_search_stats.return_value = mock_search_stats
        
        response = client.get("/api/ranking/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        # Check combined stats
        assert data["total_persons"] == 100
        assert data["total_wins"] == 500
        assert data["top_person"]["name"] == "Top Person"
        assert data["top_person"]["win_count"] == 50
        assert data["total_search_sessions"] == 1500
        assert data["total_search_results"] == 8000
        assert data["first_search_date"] == "2023-01-01T00:00:00"
        assert data["latest_search_date"] == "2023-12-31T23:59:59"
        
        # Verify database calls
        mock_ranking_db_instance.get_ranking_stats.assert_called_once()
        mock_search_db_instance.get_search_stats.assert_called_once()

    @pytest.mark.unit
    @patch('src.api.routes.ranking.is_sync_complete', return_value=True)
    @patch('src.api.routes.ranking.SearchDatabase')
    @patch('src.api.routes.ranking.RankingDatabase')
    def test_get_ranking_stats_database_error(self, mock_ranking_db, mock_search_db, mock_sync_complete, client):
        """Test ranking stats when database error occurs"""
        mock_ranking_db_instance = MagicMock()
        mock_ranking_db.return_value = mock_ranking_db_instance
        mock_ranking_db_instance.get_ranking_stats.side_effect = Exception("Database error")
        
        response = client.get("/api/ranking/stats")
        
        assert response.status_code == 500

    @pytest.mark.unit
    @patch('src.api.routes.ranking.is_sync_complete', return_value=True)
    @patch('src.api.routes.ranking.SearchDatabase')
    def test_get_search_history_success(self, mock_search_db, mock_sync_complete, client):
        """Test successful search history retrieval"""
        mock_search_db_instance = MagicMock()
        mock_search_db.return_value = mock_search_db_instance
        
        mock_history_data = [
            {
                'session_id': 'session-1',
                'search_timestamp': '2024-01-01 10:00:00',
                'metadata': {'filename': 'test1.jpg'},
                'results': []
            },
            {
                'session_id': 'session-2',
                'search_timestamp': '2024-01-01 11:00:00',
                'metadata': {'filename': 'test2.jpg'},
                'results': []
            }
        ]
        mock_search_db_instance.get_search_sessions.return_value = mock_history_data
        
        response = client.get("/api/ranking/history")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "history" in data
        assert "total_count" in data
        assert data["total_count"] == 2
        assert len(data["history"]) == 2
        
        # Check first history item
        first_item = data["history"][0]
        assert first_item["session_id"] == "session-1"
        assert first_item["search_timestamp"] == "2024-01-01 10:00:00"
        
        # Verify database call
        mock_search_db_instance.get_search_sessions.assert_called_once_with(limit=50)

    @pytest.mark.unit
    @patch('src.api.routes.ranking.is_sync_complete', return_value=True)
    @patch('src.api.routes.ranking.SearchDatabase')
    def test_get_search_history_with_person_id(self, mock_search_db, mock_sync_complete, client):
        """Test search history retrieval with person_id filter"""
        mock_search_db_instance = MagicMock()
        mock_search_db.return_value = mock_search_db_instance
        
        mock_history_data = [
            {
                'session_id': 'session-1',
                'person_id': 1,
                'search_timestamp': '2024-01-01 10:00:00'
            }
        ]
        mock_search_db_instance.get_search_history.return_value = mock_history_data
        
        response = client.get("/api/ranking/history?person_id=1")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "history" in data
        assert "total_count" in data
        assert data["total_count"] == 1
        
        # Verify database call with person_id
        mock_search_db_instance.get_search_history.assert_called_once_with(limit=50, person_id=1)

    @pytest.mark.unit
    @patch('src.api.routes.ranking.is_sync_complete', return_value=True)
    @patch('src.api.routes.ranking.SearchDatabase')
    def test_get_search_history_with_limit(self, mock_search_db, mock_sync_complete, client):
        """Test search history retrieval with custom limit"""
        mock_search_db_instance = MagicMock()
        mock_search_db.return_value = mock_search_db_instance
        mock_search_db_instance.get_search_sessions.return_value = []
        
        response = client.get("/api/ranking/history?limit=25")
        
        assert response.status_code == 200
        # Verify that limit parameter was passed correctly
        mock_search_db_instance.get_search_sessions.assert_called_once_with(limit=25)

    @pytest.mark.unit
    @patch('src.api.routes.ranking.is_sync_complete', return_value=True)
    @patch('src.api.routes.ranking.SearchDatabase')
    def test_get_search_history_database_error(self, mock_search_db, mock_sync_complete, client):
        """Test search history when database error occurs"""
        mock_search_db_instance = MagicMock()
        mock_search_db.return_value = mock_search_db_instance
        mock_search_db_instance.get_search_sessions.side_effect = Exception("Database error")
        
        response = client.get("/api/ranking/history")
        
        assert response.status_code == 500

    @pytest.mark.unit
    @patch('src.api.routes.ranking.is_sync_complete', return_value=True)
    @patch('src.api.routes.ranking.RankingDatabase')
    def test_get_ranking_empty_results(self, mock_ranking_db, mock_sync_complete, client):
        """Test ranking retrieval with empty results"""
        mock_ranking_db_instance = MagicMock()
        mock_ranking_db.return_value = mock_ranking_db_instance
        mock_ranking_db_instance.get_ranking.return_value = []
        
        response = client.get("/api/ranking")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["ranking"] == []
        assert data["total_count"] == 0

    @pytest.mark.unit
    @patch('src.api.routes.ranking.is_sync_complete', return_value=True)
    @patch('src.api.routes.ranking.SearchDatabase')
    def test_get_search_history_empty_results(self, mock_search_db, mock_sync_complete, client):
        """Test search history retrieval with empty results"""
        mock_search_db_instance = MagicMock()
        mock_search_db.return_value = mock_search_db_instance
        mock_search_db_instance.get_search_sessions.return_value = []
        
        response = client.get("/api/ranking/history")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["history"] == []
        assert data["total_count"] == 0