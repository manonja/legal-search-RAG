"""Tests for document upload functionality."""

import pytest
from pathlib import Path
from fastapi import UploadFile
from unittest.mock import Mock, patch
import shutil
import os

from app.services.documents.upload import process_uploaded_document
from app.core.config import get_settings

# Get settings
settings = get_settings()


@pytest.fixture(autouse=True)
def setup_test_directories():
    """Create test directories and clean them up after tests."""
    # Create test directories
    os.makedirs(settings.DOCS_ROOT, exist_ok=True)
    os.makedirs(settings.CHUNKS_DIR, exist_ok=True)
    os.makedirs(settings.CHROMA_DIR, exist_ok=True)

    yield

    # Clean up test directories
    if os.path.exists(settings.DOCS_ROOT):
        shutil.rmtree(settings.DOCS_ROOT)
    if os.path.exists(settings.CHUNKS_DIR):
        shutil.rmtree(settings.CHUNKS_DIR)
    if os.path.exists(settings.CHROMA_DIR):
        shutil.rmtree(settings.CHROMA_DIR)


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    return settings


@pytest.fixture
def sample_pdf_content():
    """Create sample PDF content for testing."""
    return b"%PDF-1.4\n%Test PDF content"


@pytest.fixture
def sample_docx_content():
    """Create sample DOCX content for testing."""
    return b"PK\x03\x04\x14\x00\x00\x00\x08\x00"  # Minimal DOCX header


@pytest.mark.asyncio
async def test_process_pdf_document():
    """Test processing a PDF document."""
    # Create a test PDF file
    test_file = Path(settings.DOCS_ROOT) / "test.pdf"
    test_file.write_text("Test content")

    # Create UploadFile object
    upload_file = UploadFile(
        file=open(test_file, "rb"), filename="test.pdf", content_type="application/pdf"
    )

    # Process the document
    result = await process_uploaded_document(upload_file, settings)

    # Check result
    pytest.assume(result["status"] == "success")
    pytest.assume("document_id" in result)
    pytest.assume(result["num_chunks"] > 0)


@pytest.mark.asyncio
async def test_process_docx_document():
    """Test processing a DOCX document."""
    # Create a test DOCX file
    test_file = Path(settings.DOCS_ROOT) / "test.docx"
    test_file.write_text("Test content")

    # Create UploadFile object
    upload_file = UploadFile(
        file=open(test_file, "rb"),
        filename="test.docx",
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

    # Process the document
    result = await process_uploaded_document(upload_file, settings)

    # Check result
    pytest.assume(result["status"] == "success")
    pytest.assume("document_id" in result)
    pytest.assume(result["num_chunks"] > 0)


@pytest.mark.asyncio
async def test_process_invalid_file():
    """Test processing an invalid file type."""
    # Create a test file with invalid extension
    test_file = Path(settings.DOCS_ROOT) / "test.txt"
    test_file.write_text("Test content")

    # Create UploadFile object
    upload_file = UploadFile(
        file=open(test_file, "rb"), filename="test.txt", content_type="text/plain"
    )

    # Process the document and expect an error
    with pytest.raises(ValueError) as exc_info:
        await process_uploaded_document(upload_file, settings)
    pytest.assume("Unsupported file type" in str(exc_info.value))


@pytest.mark.asyncio
async def test_unsupported_file_type(mock_settings):
    """Test handling of unsupported file types."""
    # Create mock file
    mock_file = Mock(spec=UploadFile)
    mock_file.filename = "test.txt"

    # Process document and expect error
    with pytest.raises(ValueError, match="Unsupported file type"):
        await process_uploaded_document(mock_file, mock_settings)


@pytest.mark.asyncio
async def test_empty_document(mock_settings, sample_pdf_content):
    """Test handling of empty documents."""
    # Create mock file
    mock_file = Mock(spec=UploadFile)
    mock_file.filename = "test.pdf"
    mock_file.read.return_value = sample_pdf_content

    # Mock empty text extraction
    with patch("app.services.documents.upload.extract_pdf_text") as mock_extract:
        mock_extract.return_value = ""

        # Process document and expect error
        with pytest.raises(ValueError, match="No text extracted from document"):
            await process_uploaded_document(mock_file, mock_settings)
