"""Tests for document search and query routers."""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile
import shutil
from app.main import app
from app.services.documents.search import search_documents
from app.services.documents.query import process_query
from tests.fixtures import (
    mock_search_documents_router,
    mock_process_query_router,
)
from tests.constants import TEST_QUERY

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


def test_search_documents_success(mock_search_documents_router):
    """Test successfully searching documents."""
    response = client.post("/api/search", json={"query": TEST_QUERY, "limit": 5})
    assert response.status_code == 200
    assert len(response.json()) == 2
    assert response.json()[0]["text"] == "Test document 1"
    assert response.json()[1]["text"] == "Test document 2"
    mock_search_documents_router.assert_called_once()


def test_search_documents_empty_query(mock_search_documents_router):
    """Test searching with an empty query."""
    response = client.post("/api/search", json={"query": "", "limit": 5})
    assert response.status_code == 422

    # FastAPI validation errors return a list of error details
    error_details = response.json()["detail"]
    assert isinstance(error_details, list)

    # Check if any error is related to the query field
    query_errors = [
        error
        for error in error_details
        if error.get("loc") and "query" in error.get("loc")
    ]
    assert len(query_errors) > 0

    mock_search_documents_router.assert_not_called()


def test_search_documents_error(mock_search_documents_router):
    """Test searching documents with an error."""
    mock_search_documents_router.side_effect = Exception("Search error")
    response = client.post("/api/search", json={"query": TEST_QUERY, "limit": 5})
    assert response.status_code == 500
    assert "Search error" in response.json()["detail"]
    mock_search_documents_router.assert_called_once()


def test_query_documents_success(mock_process_query_router):
    """Test successfully querying documents."""
    response = client.post("/api/query", json={"query": TEST_QUERY})
    assert response.status_code == 200
    assert response.json()["answer"] == "This is a test response"
    assert len(response.json()["sources"]) == 2
    mock_process_query_router.assert_called_once()


def test_query_documents_empty_query(mock_process_query_router):
    """Test querying with an empty query."""
    response = client.post("/api/query", json={"query": ""})
    assert response.status_code == 422

    # FastAPI validation errors return a list of error details
    error_details = response.json()["detail"]
    assert isinstance(error_details, list)

    # Check if any error is related to the query field
    query_errors = [
        error
        for error in error_details
        if error.get("loc") and "query" in error.get("loc")
    ]
    assert len(query_errors) > 0

    mock_process_query_router.assert_not_called()


def test_query_documents_error(mock_process_query_router):
    """Test querying documents with an error."""
    mock_process_query_router.side_effect = Exception("Query error")
    response = client.post("/api/query", json={"query": TEST_QUERY})
    assert response.status_code == 500
    assert "Query error" in response.json()["detail"]
    mock_process_query_router.assert_called_once()


def test_rag_search_success(mock_process_query_router):
    """Test successfully performing RAG search."""
    response = client.post(
        "/api/rag-search",
        json={
            "query": TEST_QUERY,
            "max_results": 5,
            "temperature": 0.7,
            "max_tokens": 1000,
        },
    )
    assert response.status_code == 200
    assert response.json()["answer"] == "This is a test response"
    assert len(response.json()["sources"]) == 2
    assert response.json()["confidence"] == 0.8
    mock_process_query_router.assert_called_once()
