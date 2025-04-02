import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile
import shutil
from app.main import app
from app.services.documents.search import search_documents
from app.services.documents.query import process_query

client = TestClient(app)


@pytest.fixture
def test_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)


@pytest.fixture
def mock_search_documents(mocker):
    """Mock the search_documents function."""
    mock_search = mocker.MagicMock(
        return_value=[
            {
                "text": "Test document 1",
                "metadata": {"title": "Doc 1"},
                "distance": 0.1,
            },
            {
                "text": "Test document 2",
                "metadata": {"title": "Doc 2"},
                "distance": 0.2,
            },
        ]
    )
    mocker.patch(
        "app.routers.documents.search.search_documents", return_value=mock_search
    )
    return mock_search


@pytest.fixture
def mock_process_query(mocker):
    """Mock the process_query function."""
    mock_query = mocker.MagicMock(
        return_value={
            "answer": "This is a test response",
            "sources": ["Source 1", "Source 2"],
            "confidence": 0.8,
        }
    )
    mocker.patch("app.routers.documents.query.process_query", return_value=mock_query)
    return mock_query


def test_search_documents_success(mock_search_documents):
    """Test successfully searching documents."""
    response = client.post(
        "/documents/search", json={"query": "test query", "limit": 5}
    )
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["text"] == "Test document 1"
    assert response.json()[1]["text"] == "Test document 2"
    mock_search_documents.assert_called_once()


def test_search_documents_empty_query(mock_search_documents):
    """Test searching with an empty query."""
    response = client.post("/documents/search", json={"query": "", "limit": 5})
    assert response.status_code == 400
    assert "Query cannot be empty" in response.json()["detail"]
    mock_search_documents.assert_not_called()


def test_search_documents_error(mock_search_documents):
    """Test searching documents with an error."""
    mock_search_documents.side_effect = Exception("Search error")
    response = client.post(
        "/documents/search", json={"query": "test query", "limit": 5}
    )
    assert response.status_code == 500
    assert "Search error" in response.json()["detail"]
    mock_search_documents.assert_called_once()


def test_query_documents_success(mock_process_query):
    """Test successfully querying documents."""
    response = client.post("/documents/query", json={"query": "test query"})
    assert response.status_code == 200
    assert response.json()["answer"] == "This is a test response"
    assert len(response.json()["sources"]) == 2
    mock_process_query.assert_called_once()


def test_query_documents_empty_query(mock_process_query):
    """Test querying with an empty query."""
    response = client.post("/documents/query", json={"query": ""})
    assert response.status_code == 400
    assert "Query cannot be empty" in response.json()["detail"]
    mock_process_query.assert_not_called()


def test_query_documents_error(mock_process_query):
    """Test querying documents with an error."""
    mock_process_query.side_effect = Exception("Query error")
    response = client.post("/documents/query", json={"query": "test query"})
    assert response.status_code == 500
    assert "Query error" in response.json()["detail"]
    mock_process_query.assert_called_once()
