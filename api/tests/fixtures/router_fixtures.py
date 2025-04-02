"""Router test fixtures.

This module provides fixtures specifically for testing routers.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

from app.core.config import get_settings

# Get settings
settings = get_settings()


@pytest.fixture
def test_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)


@pytest.fixture
def sample_document_content():
    """Create a sample document content."""
    return "This is a test document."


@pytest.fixture
def sample_pdf_content():
    """Create a sample PDF file with test content."""
    return b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"


@pytest.fixture
def sample_docx_content():
    """Create a sample DOCX file with test content."""
    return b"PK\x03\x04\x14\x00\x00\x00\x08\x00"


@pytest.fixture
def sample_txt_content():
    """Create a sample text file with test content."""
    return b"This is a test document."


@pytest.fixture
def test_document_file(test_dir, sample_document_content):
    """Create a test document file."""
    doc_path = test_dir / "test_doc.txt"
    doc_path.write_text(sample_document_content)
    return doc_path


@pytest.fixture
def test_pdf_file(test_dir, sample_pdf_content):
    """Create a test PDF file."""
    pdf_path = test_dir / "test.pdf"
    pdf_path.write_bytes(sample_pdf_content)
    return pdf_path


@pytest.fixture
def test_docx_file(test_dir, sample_docx_content):
    """Create a test DOCX file."""
    docx_path = test_dir / "test.docx"
    docx_path.write_bytes(sample_docx_content)
    return docx_path


@pytest.fixture
def test_txt_file(test_dir, sample_txt_content):
    """Create a test text file."""
    txt_path = test_dir / "test.txt"
    txt_path.write_bytes(sample_txt_content)
    return txt_path


# Document Router Mocks
@pytest.fixture
def mock_get_document_content(mocker):
    """Mock the get_document_content function."""
    mock_get = mocker.AsyncMock(
        return_value=("Test document content", {"title": "Test Document"})
    )
    mocker.patch(
        "app.routers.documents.document.get_document_content", side_effect=mock_get
    )
    return mock_get


# Search Router Mocks
@pytest.fixture
def mock_search_documents_router(mocker):
    """Mock the search_documents function in the router."""
    mock_search = mocker.AsyncMock(
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
        "app.routers.documents.search.search_documents", side_effect=mock_search
    )
    return mock_search


@pytest.fixture
def mock_process_query_router(mocker):
    """Mock the process_query function in the router."""
    mock_query = mocker.AsyncMock(
        return_value={
            "answer": "This is a test response",
            "sources": ["Source 1", "Source 2"],
            "confidence": 0.8,
        }
    )
    mocker.patch("app.routers.documents.query.process_query", side_effect=mock_query)
    return mock_query


# Upload Router Mocks
@pytest.fixture
def mock_process_uploaded_document_router(mocker):
    """Mock the process_uploaded_document function in the router."""
    mock_process = mocker.AsyncMock(
        return_value={"document_id": "test_id", "num_chunks": 2, "status": "success"}
    )
    mocker.patch(
        "app.routers.documents.upload.process_uploaded_document",
        side_effect=mock_process,
    )
    return mock_process
