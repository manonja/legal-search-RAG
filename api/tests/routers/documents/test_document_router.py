"""Tests for document retrieval router."""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from tests.fixtures import (
    test_dir,
    sample_document_content,
    test_document_file,
    mock_get_document_content,
)

client = TestClient(app)


def test_get_document_success(test_document_file, mock_get_document_content):
    """Test successfully retrieving a document."""
    response = client.get(f"/api/documents/{test_document_file.name}")
    assert response.status_code == 200
    assert response.json()["content"] == "Test document content"
    assert response.json()["metadata"]["title"] == "Test Document"
    mock_get_document_content.assert_called_once()


def test_get_document_not_found(mock_get_document_content):
    """Test retrieving a non-existent document."""
    mock_get_document_content.side_effect = FileNotFoundError("Document not found")
    response = client.get("/api/documents/nonexistent.txt")
    assert response.status_code == 404
    assert "Document not found" in response.json()["detail"]
    mock_get_document_content.assert_called_once()


def test_get_document_error(mock_get_document_content):
    """Test retrieving a document with an error."""
    mock_get_document_content.side_effect = IOError("Error reading document")
    response = client.get("/api/documents/test.txt")
    assert response.status_code == 500
    assert "Error reading document" in response.json()["detail"]
    mock_get_document_content.assert_called_once()


def test_get_document_invalid_id(mock_get_document_content):
    """Test retrieving a document with an invalid ID."""
    mock_get_document_content.side_effect = ValueError("Invalid document ID")
    response = client.get("/api/documents/invalid_id")
    assert response.status_code == 500
    assert "Invalid document ID" in response.json()["detail"]
    mock_get_document_content.assert_called_once()
