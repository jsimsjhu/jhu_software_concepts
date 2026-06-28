"""Module 6 tests for the microservices application."""
import pytest
import sys
import os
import json
from unittest.mock import Mock, patch

# Add the src/web directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'web'))

from run import create_app, get_all_results, background_scrape, _reset_state, _set_status, scrape_state, _state_lock
from publisher import _open_channel, publish_task
from db_helpers import get_connection, build_applicant_row, INSERT_APPLICANT_SQL


@pytest.fixture
def app():
    """Create a Flask app for testing."""
    app = create_app()
    app.config.update({
        "TESTING": True,
        "DATABASE_URL": "postgresql://app_user:app_password@db:5432/postgres",
        "RABBITMQ_URL": "amqp://guest:guest@rabbitmq:5672/"
    })
    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


def test_index_page(client):
    """Test the index page loads."""
    response = client.get("/")
    assert response.status_code == 200


def test_analysis_page(client):
    """Test the analysis page loads."""
    response = client.get("/analysis")
    assert response.status_code == 200


def test_api_scrape_endpoint(client):
    """Test the scrape API endpoint."""
    response = client.post("/api/scrape", json={})
    assert response.status_code in [202, 503]


def test_api_recompute_endpoint(client):
    """Test the recompute API endpoint."""
    response = client.post("/api/recompute", json={})
    assert response.status_code in [202, 503]


def test_api_status_endpoint(client):
    """Test the status API endpoint."""
    response = client.get("/api/status")
    assert response.status_code == 200


def test_scrape_status_endpoint(client):
    """Test the scrape status endpoint."""
    response = client.get("/scrape_status")
    assert response.status_code == 200


def test_pull_data_endpoint(client):
    """Test the pull data endpoint."""
    response = client.post("/pull-data")
    assert response.status_code in [200, 409, 503]


def test_update_analysis_endpoint(client):
    """Test the update analysis endpoint."""
    response = client.post("/update-analysis")
    assert response.status_code in [200, 409, 503]


def test_reset_state():
    """Test resetting the scrape state."""
    _reset_state()
    assert scrape_state["status"] == "idle"


def test_set_status():
    """Test setting the scrape status."""
    _set_status("running", "Test message", records_added=5)
    assert scrape_state["status"] == "running"
    assert scrape_state["message"] == "Test message"
    assert scrape_state["records_added"] == 5


@patch('src.web.db_helpers.psycopg.connect')
def test_get_connection(mock_connect):
    """Test database connection."""
    get_connection()
    mock_connect.assert_called_once()


def test_build_applicant_row():
    """Test building an applicant row."""
    entry = {
        "result_id": "123",
        "program": "CS",
        "comments": "Test",
        "added_on": "2024-01-01",
        "result_url": "http://test.com",
        "acceptance_status": "Accepted",
        "term": "Fall 2024",
        "applicant_type": "International",
        "gpa": "3.5",
        "gre_quant": "160",
        "gre_verbal": "155",
        "gre_aw": "4.0",
        "degree": "Masters"
    }
    llm_lookup = {}
    row = build_applicant_row(entry, llm_lookup)
    assert len(row) == 14
    assert row[0] == "CS"
    assert row[1] == "Test"


@patch('src.web.publisher.pika.BlockingConnection')
def test_publish_task(mock_connection):
    """Test publishing a task."""
    # Setup mock
    mock_channel = Mock()
    mock_conn = Mock()
    mock_conn.channel.return_value = mock_channel
    mock_connection.return_value = mock_conn

    # Test publish
    publish_task("test_task", {"key": "value"})

    # Verify
    mock_connection.assert_called_once()
    mock_channel.basic_publish.assert_called_once()


@patch('src.web.run.psycopg.connect')
def test_get_all_results(mock_connect):
    """Test get_all_results function."""
    # Setup mock cursor
    mock_cursor = Mock()
    mock_cursor.fetchone.side_effect = [(10,), (25.5,), (3.0, 320.0, 150.0, 4.0), (3.2,), (75.0,), (3.4,), (5,), (3,), (8,), [("Fall 2024", 100)]]
    mock_cursor.fetchall.return_value = [("Fall 2024", 100)]
    mock_conn = Mock()
    mock_conn.cursor.return_value = mock_cursor
    mock_connect.return_value = mock_conn

    # Mock current_app config
    with patch('src.web.run.current_app') as mock_app:
        mock_app.config = {"DATABASE_URL": "test_url"}

        # Call the function
        result = get_all_results()

        # Verify
        assert result["q1_fall_2026_count"] == 10
        assert result["q2_pct_international"] == 25.5
        assert mock_cursor.execute.call_count >= 10


@patch('src.web.run.psycopg.connect')
def test_background_scrape(mock_connect):
    """Test background_scrape function."""
    # Setup mock
    mock_cursor = Mock()
    mock_cursor.fetchall.return_value = []
    mock_conn = Mock()
    mock_conn.cursor.return_value = mock_cursor
    mock_connect.return_value = mock_conn

    # Create a mock app
    mock_app = Mock()
    mock_app.config = {"DATABASE_URL": "test_url"}

    # Test with no data file
    with patch('src.web.run.open', side_effect=FileNotFoundError):
        _reset_state()
        background_scrape(mock_app)
        assert scrape_state["status"] == "error"