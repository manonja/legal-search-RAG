"""Tests for document.py service functionality."""

import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.documents.document import get_document_content
from app.services.datastore import DocumentMetadata

# Sample document content for testing
SAMPLE_DOCUMENT_CONTENT = "This is a test document for testing the document service."


@pytest.fixture
def mock_datastore():
    """Fixture to create a mock datastore service."""
    mock = MagicMock()

    # Setup mock document metadata
    document_metadata = DocumentMetadata(
        document_id="test-uuid",
        original_filename="test_document.txt",
        original_file_path="/data/test-uuid/test_document.txt",
        text_file_path="/data/test-uuid/extracted_text.txt",
        document_dir="/data/test-uuid",
    )

    # Setup mock responses
    mock.get_document.return_value = document_metadata
    mock.get_text_content.return_value = SAMPLE_DOCUMENT_CONTENT

    return mock


@pytest.mark.asyncio
@patch("app.services.documents.document.get_datastore_service")
async def test_get_document_content_with_text_content(
    mock_get_datastore, mock_datastore
):
    """Test getting document content using the text extraction."""
    # Setup datastore mock
    mock_get_datastore.return_value = mock_datastore

    # Call the function with a UUID
    content, metadata = await get_document_content("test-uuid")

    # Verify datastore methods were called
    mock_datastore.get_document.assert_called_once_with("test-uuid")
    mock_datastore.get_text_content.assert_called_once_with("test-uuid")

    # Check results
    assert content == SAMPLE_DOCUMENT_CONTENT
    assert metadata["document_id"] == "test-uuid"
    assert metadata["filename"] == "test_document.txt"
    assert metadata["source"] == "datastore:test-uuid"


@pytest.mark.asyncio
@patch("app.services.documents.document.get_datastore_service")
async def test_get_document_content_with_no_text_content(
    mock_get_datastore, mock_datastore
):
    """Test that FileNotFoundError is raised when no text content is available."""
    # Setup datastore mock with no text content
    mock_get_datastore.return_value = mock_datastore
    mock_datastore.get_text_content.return_value = None

    # Check that FileNotFoundError is raised
    with pytest.raises(FileNotFoundError) as excinfo:
        await get_document_content("test-uuid")

    # Verify datastore methods were called
    mock_datastore.get_document.assert_called_once_with("test-uuid")
    mock_datastore.get_text_content.assert_called_once_with("test-uuid")

    # Check error message
    assert "No extracted text found for document" in str(excinfo.value)


@pytest.mark.asyncio
@patch("app.services.documents.document.get_datastore_service")
async def test_get_document_content_not_found(mock_get_datastore, mock_datastore):
    """Test getting content for a document that doesn't exist."""
    # Setup datastore mock to return None for document
    mock_get_datastore.return_value = mock_datastore
    mock_datastore.get_document.return_value = None

    # Check that FileNotFoundError is raised
    with pytest.raises(FileNotFoundError):
        await get_document_content("nonexistent-uuid")
