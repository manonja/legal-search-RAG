"""Integration tests for the FastAPI endpoints."""

import asyncio
import os
import shutil
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app

# Set testing environment variable
os.environ["TESTING"] = "true"

# Test data
TEST_QUERY = "What are the legal requirements for contracts?"
TEST_DOCUMENT_ID = "test_document.txt"
TEST_DOCUMENT_CONTENT = "This is a test document for integration testing."


@pytest.fixture
def test_client() -> Generator:
    """Create a test client for the FastAPI app."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
async def async_client() -> AsyncGenerator:
    """Create an async test client for the FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def test_document(tmp_path: Path) -> Generator:
    """Create a test document for testing document retrieval."""
    doc_path = tmp_path / TEST_DOCUMENT_ID
    doc_path.write_text(TEST_DOCUMENT_CONTENT)
    yield doc_path
    doc_path.unlink(missing_ok=True)


def test_health_check(test_client: TestClient) -> None:
    """Test the health check endpoint."""
    response = test_client.get("/health")
    assert response.status_code == 200  # noqa: S101
    assert response.json() == {"status": "ok", "version": "1.0.0"}  # noqa: S101


def test_search_documents(test_client: TestClient) -> None:
    """Test the search documents endpoint."""
    response = test_client.post("/search", json={"query": TEST_QUERY, "limit": 5})
    assert response.status_code == 200  # noqa: S101
    results = response.json()
    assert isinstance(results, list)  # noqa: S101


def test_legacy_search_documents(test_client: TestClient) -> None:
    """Test the legacy search documents endpoint."""
    response = test_client.post(
        "/api/search",
        json={
            "query_text": TEST_QUERY,
            "n_results": 3,
            "min_similarity": 0.7,
            "metadata_filter": None,
        },
    )
    assert response.status_code == 200  # noqa: S101
    data = response.json()
    assert "results" in data  # noqa: S101
    assert "total_found" in data  # noqa: S101
    assert isinstance(data["results"], list)  # noqa: S101
    assert isinstance(data["total_found"], int)  # noqa: S101


def test_rag_search(test_client: TestClient) -> None:
    """Test the RAG search endpoint."""
    response = test_client.post(
        "/rag-search",
        json={"query": TEST_QUERY, "limit": 5, "max_tokens": 1000, "temperature": 0.7},
    )
    assert response.status_code == 200  # noqa: S101
    data = response.json()
    assert "answer" in data  # noqa: S101
    assert "sources" in data  # noqa: S101
    assert "total_tokens" in data  # noqa: S101
    assert isinstance(data["answer"], str)  # noqa: S101
    assert isinstance(data["sources"], list)  # noqa: S101
    assert isinstance(data["total_tokens"], int)  # noqa: S101


def test_upload_document(test_client: TestClient, test_document: Path) -> None:
    """Test document upload endpoint."""
    with open(test_document, "rb") as f:
        files = {"file": (TEST_DOCUMENT_ID, f, "text/plain")}
        response = test_client.post("/api/documents/upload", files=files)

    assert response.status_code == 200  # noqa: S101
    data = response.json()
    assert "message" in data  # noqa: S101
    assert "document_id" in data  # noqa: S101
    assert data["document_id"] == TEST_DOCUMENT_ID  # noqa: S101


def test_get_document(test_client: TestClient, test_document: Path) -> None:
    """Test the document retrieval endpoint."""
    # First upload the document
    with open(test_document, "rb") as f:
        files = {"file": (TEST_DOCUMENT_ID, f, "text/plain")}
        upload_response = test_client.post("/api/documents/upload", files=files)

    assert upload_response.status_code == 200  # noqa: S101

    # Then try to retrieve it
    response = test_client.get(f"/api/documents/{TEST_DOCUMENT_ID}")
    assert response.status_code == 200  # noqa: S101
    data = response.json()
    assert "content" in data  # noqa: S101
    assert "metadata" in data  # noqa: S101
    assert "source" in data  # noqa: S101
    assert "chunks" in data  # noqa: S101
    assert data["content"] == TEST_DOCUMENT_CONTENT  # noqa: S101


def test_get_document_not_found(test_client: TestClient) -> None:
    """Test document retrieval with non-existent document."""
    response = test_client.get("/api/documents/nonexistent.txt")
    assert response.status_code == 404  # noqa: S101
    assert "Document not found" in response.json()["detail"]  # noqa: S101


def test_cors_middleware(test_client: TestClient) -> None:
    """Test that CORS middleware is properly configured."""
    response = test_client.options(
        "/search",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code == 200  # noqa: S101
    assert "access-control-allow-origin" in response.headers  # noqa: S101
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"  # noqa: S101
