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
    # Create a mock collection
    mock_collection = mocker.MagicMock()
    mock_collection.add = mocker.MagicMock()

    # Create a mock client
    mock_client = mocker.MagicMock()
    mock_client.get_or_create_collection.return_value = mock_collection

    # Patch the PersistentClient in the embeddings module
    mocker.patch(
        "app.services.embeddings.chromadb.PersistentClient", return_value=mock_client
    )

    return mock_client


@pytest.fixture
def mock_openai_client(mocker):
    """Mock the OpenAI client."""
    mock_client = mocker.MagicMock()

    # We need to patch the embedding_functions.OpenAIEmbeddingFunction
    mock_embedding_function = mocker.MagicMock()
    mocker.patch(
        "app.services.embeddings.embedding_functions.OpenAIEmbeddingFunction",
        return_value=mock_embedding_function,
    )

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
    mock_process = mocker.patch("app.services.documents.upload.process_chunks")
    return mock_process


@pytest.fixture
def mock_extract_pdf(mocker):
    """Mock the extract_pdf_text function."""
    mock_extract = mocker.patch(
        "app.services.documents.upload.extract_pdf_text",
        return_value="Test PDF content",
    )
    return mock_extract


@pytest.fixture
def mock_extract_docx(mocker):
    """Mock the extract_docx_text function."""
    mock_extract = mocker.patch(
        "app.services.documents.upload.extract_docx_text",
        return_value="Test DOCX content",
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
    # Create a mock UploadFile object
    mock_file = Mock(spec=UploadFile)
    mock_file.filename = test_pdf_file.name

    # Mock the file.read method to return bytes
    mock_file.read = AsyncMock()
    # We need to set the return_value directly, not when creating the AsyncMock
    mock_file.read.return_value = test_pdf_file.read_bytes()

    result = await process_uploaded_document(mock_file, settings)
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
    # Create a mock UploadFile object
    mock_file = Mock(spec=UploadFile)
    mock_file.filename = test_docx_file.name

    # Mock the file.read method to return bytes
    mock_file.read = AsyncMock()
    mock_file.read.return_value = test_docx_file.read_bytes()

    result = await process_uploaded_document(mock_file, settings)
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
    # Create a mock UploadFile object
    mock_file = Mock(spec=UploadFile)
    mock_file.filename = test_txt_file.name

    # Mock the file.read method to return bytes
    mock_file.read = AsyncMock()
    mock_file.read.return_value = test_txt_file.read_bytes()

    with pytest.raises(ValueError) as exc_info:
        await process_uploaded_document(mock_file, settings)
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
    # Create a mock UploadFile object
    mock_file = Mock(spec=UploadFile)
    mock_file.filename = test_pdf_file.name

    # Mock the file.read method to return bytes
    mock_file.read = AsyncMock()
    mock_file.read.return_value = test_pdf_file.read_bytes()

    mock_extract_pdf.return_value = ""
    with pytest.raises(ValueError) as exc_info:
        await process_uploaded_document(mock_file, settings)
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
    # Create a mock UploadFile object
    mock_file = Mock(spec=UploadFile)
    mock_file.filename = test_pdf_file.name

    # Mock the file.read method to return bytes
    mock_file.read = AsyncMock()
    mock_file.read.return_value = test_pdf_file.read_bytes()

    mock_extract_pdf.side_effect = Exception("Test error")
    with pytest.raises(Exception) as exc_info:
        await process_uploaded_document(mock_file, settings)
    assert "Test error" in str(exc_info.value)
    mock_text_splitter.split_text.assert_not_called()
    mock_process_chunks.assert_not_called()
