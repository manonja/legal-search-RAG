"""Tests for document upload functionality."""

import pytest
from pathlib import Path
from fastapi import UploadFile
from unittest.mock import Mock, patch, AsyncMock
import shutil
import os
import aiofiles
import tempfile
from app.services.documents.upload import process_uploaded_document
from app.services.process_docs import extract_pdf_text, extract_docx_text
from app.services.embeddings import process_chunks
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
def mock_chroma_client(mocker):
    """Mock the ChromaDB client."""
    mock_client = mocker.MagicMock()
    mocker.patch("app.services.embeddings.get_chroma_client", return_value=mock_client)
    return mock_client


@pytest.fixture
def mock_openai_client(mocker):
    """Mock the OpenAI client."""
    mock_client = mocker.MagicMock()
    mocker.patch("app.services.embeddings.get_openai_client", return_value=mock_client)
    return mock_client


@pytest.fixture
def mock_text_splitter(mocker):
    """Mock the text splitter."""
    mock_splitter = mocker.MagicMock()
    mock_splitter.split_text.return_value = ["chunk1", "chunk2"]
    mocker.patch(
        "app.services.documents.upload.create_text_splitter", return_value=mock_splitter
    )
    return mock_splitter


@pytest.fixture
def mock_process_chunks(mocker):
    """Mock the process_chunks function."""
    mock_process = mocker.MagicMock()
    mocker.patch(
        "app.services.documents.upload.process_chunks", return_value=mock_process
    )
    return mock_process


@pytest.fixture
def mock_extract_pdf(mocker):
    """Mock the extract_pdf_text function."""
    mock_extract = mocker.MagicMock(return_value="Test PDF content")
    mocker.patch(
        "app.services.documents.upload.extract_pdf_text", return_value=mock_extract
    )
    return mock_extract


@pytest.fixture
def mock_extract_docx(mocker):
    """Mock the extract_docx_text function."""
    mock_extract = mocker.MagicMock(return_value="Test DOCX content")
    mocker.patch(
        "app.services.documents.upload.extract_docx_text", return_value=mock_extract
    )
    return mock_extract


@pytest.mark.asyncio
async def test_process_pdf_document(
    test_pdf_file,
    mock_chroma_client,
    mock_openai_client,
    mock_text_splitter,
    mock_process_chunks,
    mock_extract_pdf,
):
    """Test processing a PDF document."""
    result = await process_uploaded_document(test_pdf_file, settings)
    assert result["status"] == "success"
    assert result["document_id"] == test_pdf_file.name
    assert result["num_chunks"] == 2
    mock_extract_pdf.assert_called_once()
    mock_text_splitter.split_text.assert_called_once()
    mock_process_chunks.assert_called_once()


@pytest.mark.asyncio
async def test_process_docx_document(
    test_docx_file,
    mock_chroma_client,
    mock_openai_client,
    mock_text_splitter,
    mock_process_chunks,
    mock_extract_docx,
):
    """Test processing a DOCX document."""
    result = await process_uploaded_document(test_docx_file, settings)
    assert result["status"] == "success"
    assert result["document_id"] == test_docx_file.name
    assert result["num_chunks"] == 2
    mock_extract_docx.assert_called_once()
    mock_text_splitter.split_text.assert_called_once()
    mock_process_chunks.assert_called_once()


@pytest.mark.asyncio
async def test_process_unsupported_file(
    test_txt_file,
    mock_chroma_client,
    mock_openai_client,
    mock_text_splitter,
    mock_process_chunks,
):
    """Test processing an unsupported file type."""
    with pytest.raises(ValueError) as exc_info:
        await process_uploaded_document(test_txt_file, settings)
    assert "Unsupported file type" in str(exc_info.value)
    mock_text_splitter.split_text.assert_not_called()
    mock_process_chunks.assert_not_called()


@pytest.mark.asyncio
async def test_process_empty_document(
    test_pdf_file,
    mock_chroma_client,
    mock_openai_client,
    mock_text_splitter,
    mock_process_chunks,
    mock_extract_pdf,
):
    """Test processing a document with no content."""
    mock_extract_pdf.return_value = ""
    with pytest.raises(ValueError) as exc_info:
        await process_uploaded_document(test_pdf_file, settings)
    assert "No text extracted from document" in str(exc_info.value)
    mock_text_splitter.split_text.assert_not_called()
    mock_process_chunks.assert_not_called()


@pytest.mark.asyncio
async def test_process_document_with_error(
    test_pdf_file,
    mock_chroma_client,
    mock_openai_client,
    mock_text_splitter,
    mock_process_chunks,
    mock_extract_pdf,
):
    """Test processing a document with an error."""
    mock_extract_pdf.side_effect = Exception("Test error")
    with pytest.raises(Exception) as exc_info:
        await process_uploaded_document(test_pdf_file, settings)
    assert "Test error" in str(exc_info.value)
    mock_text_splitter.split_text.assert_not_called()
    mock_process_chunks.assert_not_called()
