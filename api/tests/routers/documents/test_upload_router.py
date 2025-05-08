"""Tests for document upload router."""

import os
import shutil
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app
from app.services.documents.upload import process_uploaded_document
from app.services.embeddings import process_chunks
from app.services.document_processor.loaders.pdf_loader import PDFLoader
from app.services.document_processor.loaders.docx_loader import DOCXLoader
from tests.fixtures import (
    mock_process_uploaded_document_router,
    test_dir,
    test_docx_file,
    test_pdf_file,
    test_txt_file,
)

# Get settings
settings = get_settings()

# Create test client
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_test_directories():
    """Create test directories and clean them up after tests."""
    # Create test directories
    os.makedirs(settings.CHROMA_DIR, exist_ok=True)
    os.makedirs(settings.DATA_DIR, exist_ok=True)

    yield

    # Clean up test directories
    if os.path.exists(settings.CHROMA_DIR):
        shutil.rmtree(settings.CHROMA_DIR)
    if os.path.exists(settings.DATA_DIR):
        shutil.rmtree(settings.DATA_DIR)


@pytest.fixture
def test_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)


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


@pytest.fixture
def mock_process_uploaded_document(mocker):
    """Mock the process_uploaded_document function."""
    mock_process = mocker.MagicMock(
        return_value={"document_id": "test_id", "num_chunks": 2, "status": "success"}
    )
    mocker.patch(
        "app.routers.documents.upload.process_uploaded_document",
        return_value=mock_process,
    )
    return mock_process


def test_upload_pdf_document(test_pdf_file, mock_process_uploaded_document_router):
    """Test uploading a PDF document."""
    with open(test_pdf_file, "rb") as f:
        response = client.post(
            "/api/documents/upload", files={"file": ("test.pdf", f, "application/pdf")}
        )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["message"] == "Document processed successfully"
    assert "document_id" in response.json()
    mock_process_uploaded_document_router.assert_called_once()


def test_upload_docx_document(test_docx_file, mock_process_uploaded_document_router):
    """Test uploading a DOCX document."""
    with open(test_docx_file, "rb") as f:
        response = client.post(
            "/api/documents/upload",
            files={
                "file": (
                    "test.docx",
                    f,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            },
        )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["message"] == "Document processed successfully"
    assert "document_id" in response.json()
    mock_process_uploaded_document_router.assert_called_once()


def test_upload_docx_with_octet_stream(
    test_docx_file, mock_process_uploaded_document_router
):
    """Test uploading a DOCX with application/octet-stream content type.

    This simulates what happens when curl uploads a file without specifying
    the correct content type, which is what's happening in the command line scenario.
    """
    with open(test_docx_file, "rb") as f:
        response = client.post(
            "/api/documents/upload",
            files={
                "file": (
                    "test.docx",
                    f,
                    "application/octet-stream",  # Generic binary content type
                )
            },
        )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["message"] == "Document processed successfully"
    assert "document_id" in response.json()
    mock_process_uploaded_document_router.assert_called_once()


def test_upload_unsupported_file(test_txt_file, mock_process_uploaded_document_router):
    """Test uploading an unsupported file type."""
    with open(test_txt_file, "rb") as f:
        response = client.post(
            "/api/documents/upload", files={"file": ("test.txt", f, "text/plain")}
        )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]
    mock_process_uploaded_document_router.assert_not_called()


def test_upload_empty_file(test_dir, mock_process_uploaded_document_router):
    """Test uploading an empty file."""
    empty_file = test_dir / "empty.pdf"
    empty_file.touch()

    # Configure the mock to raise an error for empty files
    mock_process_uploaded_document_router.side_effect = ValueError(
        "No text extracted from document"
    )

    with open(empty_file, "rb") as f:
        response = client.post(
            "/api/documents/upload", files={"file": ("empty.pdf", f, "application/pdf")}
        )
    assert response.status_code == 400
    assert "No text extracted from document" in response.json()["detail"]
    mock_process_uploaded_document_router.assert_called_once()


def test_upload_with_error(test_pdf_file, mock_process_uploaded_document_router):
    """Test uploading a document with an error."""
    mock_process_uploaded_document_router.side_effect = Exception("Test error")
    with open(test_pdf_file, "rb") as f:
        response = client.post(
            "/api/documents/upload", files={"file": ("test.pdf", f, "application/pdf")}
        )
    assert response.status_code == 500
    assert "Test error" in response.json()["detail"]
    mock_process_uploaded_document_router.assert_called_once()
