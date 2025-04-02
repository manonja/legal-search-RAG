"""Document-related fixtures for tests."""

import pytest
from unittest.mock import MagicMock
from pathlib import Path

from tests.constants import MOCK_PDF_TEXT, MOCK_DOCX_TEXT, MOCK_DOCUMENT_CHUNKS


@pytest.fixture
def mock_extract_pdf_text(mocker):
    """Mock the PDF text extraction function."""
    mock_extract = mocker.MagicMock(return_value=MOCK_PDF_TEXT)
    mocker.patch("app.services.documents.upload.extract_pdf_text", new=mock_extract)
    return mock_extract


@pytest.fixture
def mock_extract_docx_text(mocker):
    """Mock the DOCX text extraction function."""
    mock_extract = mocker.MagicMock(return_value=MOCK_DOCX_TEXT)
    mocker.patch("app.services.documents.upload.extract_docx_text", new=mock_extract)
    return mock_extract


@pytest.fixture
def mock_create_text_splitter(mocker):
    """Mock the text splitter creation function."""
    mock_splitter = mocker.MagicMock()
    mock_splitter.split_text.return_value = MOCK_DOCUMENT_CHUNKS
    mock_create = mocker.MagicMock(return_value=mock_splitter)
    mocker.patch("app.services.documents.upload.create_text_splitter", new=mock_create)
    return mock_create


@pytest.fixture
def mock_process_chunks(mocker):
    """Mock the chunk processing function."""
    mock_process = mocker.MagicMock()
    mocker.patch("app.services.documents.upload.process_chunks", new=mock_process)
    return mock_process


@pytest.fixture
def mock_process_uploaded_document(mocker):
    """Mock the document processing function."""
    mock_process = mocker.AsyncMock(
        return_value={
            "document_id": "test_document.pdf",
            "num_chunks": 3,
            "status": "success",
        }
    )
    mocker.patch(
        "app.services.documents.upload.process_uploaded_document", new=mock_process
    )
    return mock_process


@pytest.fixture
def mock_document_service(mocker):
    """Mock the document service functions."""
    # Mock document content
    mock_content = "This is the content of the sample PDF document."
    mock_metadata = {
        "filename": "sample.pdf",
        "size": 1024,
        "last_modified": "2023-01-01T12:00:00",
        "source": "local:/path/to/sample.pdf",
    }

    # Mock get_document_content function to always return the mock content
    # regardless of the document_id passed
    async def mock_get_content(document_id):
        return mock_content, mock_metadata

    # Apply the mock directly to the endpoint function
    mocker.patch(
        "app.routers.documents.document.get_document_content",
        side_effect=mock_get_content,
    )

    return {
        "get_content": mock_get_content,
        "content": mock_content,
        "metadata": mock_metadata,
    }


@pytest.fixture
def mock_document_not_found(mocker):
    """Mock document service to return a not found error."""

    async def mock_get_content_error(document_id):
        raise FileNotFoundError(f"Document not found: {document_id}")

    mocker.patch(
        "app.routers.documents.document.get_document_content",
        side_effect=mock_get_content_error,
    )
