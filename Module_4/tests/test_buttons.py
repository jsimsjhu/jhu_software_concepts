"""
Tests for the Flask button endpoints using pytest and Flask test client.

Uses an in-memory BUSY config flag to simulate the "in-progress" state
without actually running the scraper or needing a real database.
"""

import pytest
from src.app import create_app


@pytest.fixture
def client():
    """Create a test client with database disabled (no real DB needed)."""
    app = create_app({"TESTING": True, "DATABASE_URL": None})
    with app.test_client() as client:
        yield client


@pytest.fixture
def busy_client():
    """
    Create a test client with ``BUSY=True`` to simulate an in-progress
    data pull, without actually running the scraper.
    """
    app = create_app({
        "TESTING": True,
        "DATABASE_URL": None,
        "BUSY": True,        # ← signals "pull in progress" to both endpoints
    })
    with app.test_client() as client:
        yield client


# ------------------------------------------------------------------
# 1. POST /pull-data returns 200 when not busy
# ------------------------------------------------------------------

def test_pull_data_returns_200_when_not_busy(client):
    """
    When no pull is in progress and the database is disabled,
    the endpoint returns a JSON response with success=False
    (because DB is unavailable), but still returns HTTP 200
    (it handled the request gracefully).
    """
    response = client.post("/pull-data")
    assert response.status_code == 200
    data = response.get_json()
    assert data is not None
    # DB is disabled, so it won't start a pull
    assert data["success"] is False
    assert "Database is not available" in data["message"]


# ------------------------------------------------------------------
# 2. POST /update-analysis returns 200 when not busy
# ------------------------------------------------------------------

def test_update_analysis_returns_200_when_not_busy(client):
    """
    When no pull is happening, the update-analysis endpoint should
    return HTTP 200. Since the DB is disabled, success will be False
    but the app handles it gracefully.
    """
    response = client.post("/update-analysis")
    assert response.status_code == 200
    data = response.get_json()
    assert data is not None
    assert data["success"] is False
    assert "Failed to update analysis" in data["message"]


# ------------------------------------------------------------------
# 3. POST /update-analysis returns 409 when busy
# ------------------------------------------------------------------

def test_update_analysis_returns_409_when_busy(busy_client):
    """
    When a data pull is in progress (simulated via BUSY=True),
    /update-analysis should return HTTP 409 Conflict.
    """
    response = busy_client.post("/update-analysis")
    assert response.status_code == 409
    data = response.get_json()
    assert data is not None
    assert data["success"] is False
    assert "in progress" in data["message"].lower()


# ------------------------------------------------------------------
# 4. POST /pull-data returns 409 when busy
# ------------------------------------------------------------------

def test_pull_data_returns_409_when_busy(busy_client):
    """
    When a data pull is already in progress (simulated via BUSY=True),
    /pull-data should return HTTP 409 Conflict.
    """
    response = busy_client.post("/pull-data")
    assert response.status_code == 409
    data = response.get_json()
    assert data is not None
    assert data["success"] is False
    assert "in progress" in data["message"].lower()
