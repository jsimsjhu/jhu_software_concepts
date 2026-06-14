import pytest
from src.app import create_app

@pytest.fixture
def client():
    app = create_app({"TESTING": True, "DATABASE_URL": None})
    with app.test_client() as client:
        yield client

def test_analysis_page_status(client):
    response = client.get('/analysis')
    assert response.status_code == 200

def test_analysis_page_contains_analysis_text(client):
    response = client.get('/analysis')
    assert b'Analysis' in response.data

def test_analysis_page_contains_buttons(client):
    response = client.get('/analysis')
    assert b'data-testid="pull-data-btn"' in response.data
    assert b'data-testid="update-analysis-btn"' in response.data

def test_analysis_page_contains_answer_label(client):
    response = client.get('/analysis')
    assert b'Answer:' in response.data