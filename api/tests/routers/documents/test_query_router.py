"""Tests for document query router."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from tests.constants import TEST_QUERY
from tests.fixtures import mock_process_query_router

client = TestClient(app)


def test_query_documents_success(mock_process_query_router):
    """Test successfully querying documents."""
    response = client.post(
        "/api/query",
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
    assert response.json()["sources"] == ["Source 1", "Source 2"]
    assert response.json()["confidence"] == 0.8
    mock_process_query_router.assert_called_once()


def test_query_documents_empty_query(mock_process_query_router):
    """Test querying with an empty query."""
    response = client.post(
        "/api/query", json={"query": "", "max_results": 5, "temperature": 0.7}
    )
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


def test_query_documents_missing_query(mock_process_query_router):
    """Test querying with a missing query field."""
    response = client.post("/api/query", json={"max_results": 5, "temperature": 0.7})
    assert response.status_code == 422
    mock_process_query_router.assert_not_called()


def test_query_documents_invalid_params(mock_process_query_router):
    """Test querying with invalid parameters."""
    response = client.post(
        "/api/query",
        json={
            "query": TEST_QUERY,
            "max_results": "invalid",  # Should be an integer
            "temperature": 0.7,
        },
    )
    assert response.status_code == 422
    mock_process_query_router.assert_not_called()


def test_query_documents_error(mock_process_query_router):
    """Test querying documents with an error."""
    mock_process_query_router.side_effect = Exception("Query error")
    response = client.post(
        "/api/query", json={"query": TEST_QUERY, "max_results": 5, "temperature": 0.7}
    )
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


def test_rag_search_empty_query(mock_process_query_router):
    """Test RAG search with an empty query."""
    response = client.post(
        "/api/rag-search", json={"query": "", "max_results": 5, "temperature": 0.7}
    )
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


def test_rag_search_with_custom_params(mock_process_query_router):
    """Test RAG search with custom parameters."""
    response = client.post(
        "/api/rag-search",
        json={
            "query": TEST_QUERY,
            "max_results": 10,  # Custom value
            "temperature": 0.3,  # Custom value
            "max_tokens": 500,  # Custom value
        },
    )
    assert response.status_code == 200

    # Verify the right parameters were passed
    call_args = mock_process_query_router.call_args[1]
    assert call_args["query"] == TEST_QUERY
    assert call_args["max_results"] == 10
    assert call_args["temperature"] == 0.3
    assert call_args["max_tokens"] == 500


def test_rag_search_error(mock_process_query_router):
    """Test RAG search with an error."""
    mock_process_query_router.side_effect = Exception("RAG search error")
    response = client.post(
        "/api/rag-search",
        json={
            "query": TEST_QUERY,
            "max_results": 5,
            "temperature": 0.7,
            "max_tokens": 1000,
        },
    )
    assert response.status_code == 500
    assert "RAG search error" in response.json()["detail"]
    mock_process_query_router.assert_called_once()
