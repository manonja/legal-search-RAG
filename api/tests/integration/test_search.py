"""Integration tests for search and RAG endpoints."""

from fastapi.testclient import TestClient
from tests.constants import TEST_QUERY, MOCK_SEARCH_RESULT_TEXT


def test_search_documents(test_client: TestClient, mock_chroma_collection) -> None:
    """Test the search documents endpoint."""
    response = test_client.post("/api/search", json={"query": TEST_QUERY, "limit": 5})
    assert response.status_code == 200  # noqa: S101
    assert len(response.json()) > 0
    assert "text" in response.json()[0]
    assert "metadata" in response.json()[0]
    assert "distance" in response.json()[0]
    assert response.json()[0]["text"] == MOCK_SEARCH_RESULT_TEXT
    assert response.json()[0]["metadata"]["source"] == "test_doc.pdf"
    assert response.json()[0]["distance"] == 0.5


def test_legacy_search_documents(
    test_client: TestClient, mock_chroma_collection
) -> None:
    """Test the legacy search documents endpoint."""
    response = test_client.post(
        "/api/search/api",
        json={
            "query_text": TEST_QUERY,
            "n_results": 3,
            "min_similarity": 0.7,
            "metadata_filter": None,
        },
    )
    assert response.status_code == 200  # noqa: S101
    assert "results" in response.json()
    assert "total_found" in response.json()
    assert len(response.json()["results"]) > 0
    assert response.json()["results"][0]["text"] == MOCK_SEARCH_RESULT_TEXT
    assert response.json()["results"][0]["metadata"]["source"] == "test_doc.pdf"
    assert response.json()["results"][0]["distance"] == 0.5


def test_rag_search(
    test_client: TestClient, mock_chroma_collection, mock_openai_client
) -> None:
    """Test the RAG search endpoint."""
    response = test_client.post(
        "/api/rag-search",
        json={
            "query": TEST_QUERY,
            "max_results": 5,
            "temperature": 0.7,
            "max_tokens": 1000,
        },
    )
    assert response.status_code == 200  # noqa: S101
    assert "answer" in response.json()
    assert "sources" in response.json()
    assert "confidence" in response.json()
    assert isinstance(response.json()["sources"], list)
    assert isinstance(response.json()["confidence"], float)
