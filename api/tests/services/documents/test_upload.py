"""Tests for document upload functionality."""

import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import aiofiles
import pytest
from fastapi import UploadFile

from app.core.config import get_settings
from app.services.datastore import DocumentMetadata
from app.services.documents.upload import process_uploaded_document
from app.services.embeddings import process_chunks
from app.services.document_processor.loaders.pdf_loader import PDFLoader
from app.services.document_processor.loaders.docx_loader import DOCXLoader

# Get settings
settings = get_settings()

# Mock constants for text extraction
MOCK_PDF_TEXT = "This is a test PDF document content."
MOCK_DOCX_TEXT = "This is a test DOCX document content."


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

    # Patch the PersistentClient in the correct location
    mocker.patch(
        "app.services.database.chroma.chromadb.PersistentClient",
        return_value=mock_client,
    )

    return mock_client


@pytest.fixture
def mock_openai_client(mocker):
    """Mock the OpenAI client."""
    mock_client = mocker.MagicMock()

    # We need to patch the embedding function
    mock_embedding_function = mocker.MagicMock()
    mocker.patch(
        "app.services.database.embedding_function.HuggingFaceEmbeddingFunction",
        return_value=mock_embedding_function,
    )

    return mock_client


@pytest.fixture
def mock_text_splitter(mocker):
    """Mock the text splitter."""
    mock_chunker_fn = mocker.MagicMock()
    mock_chunker_fn.return_value = [
        "Chunk 1",
        "Chunk 2",
        "Chunk 3",
    ]
    mock_chunkerify = mocker.patch("app.services.documents.upload.semchunk.chunkerify")
    mock_chunkerify.return_value = mock_chunker_fn
    return mock_chunker_fn  # Return the chunker function for assertions


@pytest.fixture
def mock_process_chunks(mocker):
    """Mock the process_chunks function."""
    return mocker.patch("app.services.documents.upload.process_chunks")


@pytest.fixture
def mock_pdf_loader(mocker):
    """Mock PDF text extraction."""
    mock_load = mocker.MagicMock(return_value=(MOCK_PDF_TEXT, {}))
    mock_loader = mocker.MagicMock()
    mock_loader.load = mock_load
    mocker.patch(
        "app.services.documents.upload.PDFLoader",
        return_value=mock_loader,
    )
    return mock_load


@pytest.fixture
def mock_docx_loader(mocker):
    """Mock DOCX text extraction."""
    mock_load = mocker.MagicMock(return_value=(MOCK_DOCX_TEXT, {}))
    mock_loader = mocker.MagicMock()
    mock_loader.load = mock_load
    mocker.patch(
        "app.services.documents.upload.DOCXLoader",
        return_value=mock_loader,
    )
    return mock_load


@pytest.fixture
def mock_datastore_service(mocker):
    """Mock the datastore service."""
    # Create a mock DocumentMetadata instance
    test_metadata = DocumentMetadata(
        document_id="test-uuid-12345",
        original_filename="test.pdf",
        original_file_path="/data/test-uuid-12345/original.pdf",
        text_file_path="/data/test-uuid-12345/extracted_text.txt",
        document_dir="/data/test-uuid-12345",
    )

    mock_datastore = mocker.MagicMock()
    mock_datastore.save_document = AsyncMock(return_value=test_metadata)

    mocker.patch(
        "app.services.documents.upload.get_datastore_service",
        return_value=mock_datastore,
    )
    return mock_datastore


@pytest.mark.asyncio
async def test_process_uploaded_document_success(
    test_pdf_file,
    mock_chroma_client,
    mock_openai_client,
    mock_text_splitter,
    mock_process_chunks,
    mock_pdf_loader,
    mock_datastore_service,
):
    """Test successful processing of an uploaded document."""
    # Create a mock UploadFile object
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "test_document.pdf"
    mock_file.content_type = "application/pdf"
    mock_file.seek = AsyncMock()
    mock_file.read = AsyncMock(return_value=b"dummy pdf content")

    # Configure the mock datastore to return specific metadata
    expected_metadata = DocumentMetadata(
        document_id="test-uuid-123",
        original_filename="test_document.pdf",
        original_file_path="/data/test-uuid-123/test_document.pdf",
        text_file_path="/data/test-uuid-123/extracted_text.txt",
        document_dir="/data/test-uuid-123",
    )
    mock_datastore_service.save_document.return_value = expected_metadata

    # Call the function
    result = await process_uploaded_document(mock_file, settings)

    # Verify calls
    mock_pdf_loader.assert_called_once()
    mock_datastore_service.save_document.assert_called_once()
    # Check that save_document was called with the file and extracted text
    call_args, _ = mock_datastore_service.save_document.call_args
    assert call_args[0] == mock_file
    assert call_args[1] == MOCK_PDF_TEXT

    # Verify chunker was called with the right parameters
    mock_text_splitter.assert_called_once_with(
        MOCK_PDF_TEXT, overlap=settings.SEMCHUNK_OVERLAP_TOKENS
    )
    mock_process_chunks.assert_called_once()
    # Verify the arguments passed to process_chunks
    args, kwargs = mock_process_chunks.call_args
    assert "chunks" in kwargs
    assert "chroma_dir" in kwargs
    assert "document_metadata" in kwargs
    assert kwargs["chroma_dir"] == settings.CHROMA_DIR
    assert kwargs["document_metadata"] == expected_metadata.model_dump()
    assert len(kwargs["chunks"]) == 3

    # Verify result
    assert result["document_id"] == expected_metadata.document_id
    assert result["original_filename"] == expected_metadata.original_filename
    assert result["num_chunks"] == 3  # Based on mock_text_splitter


@pytest.mark.asyncio
async def test_process_uploaded_document_docx(
    test_docx_file,
    mock_chroma_client,
    mock_openai_client,
    mock_text_splitter,
    mock_process_chunks,
    mock_docx_loader,
    mock_datastore_service,
):
    """Test successful processing of a DOCX document."""
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "test_document.docx"
    mock_file.content_type = (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    mock_file.seek = AsyncMock()
    mock_file.read = AsyncMock(return_value=b"dummy docx content")

    expected_metadata = DocumentMetadata(
        document_id="test-uuid-456",
        original_filename="test_document.docx",
        original_file_path="/data/test-uuid-456/test_document.docx",
        text_file_path="/data/test-uuid-456/extracted_text.txt",
        document_dir="/data/test-uuid-456",
    )
    mock_datastore_service.save_document.return_value = expected_metadata

    result = await process_uploaded_document(mock_file, settings)

    mock_docx_loader.assert_called_once()
    mock_datastore_service.save_document.assert_called_once()
    call_args, _ = mock_datastore_service.save_document.call_args
    assert call_args[0] == mock_file
    assert call_args[1] == MOCK_DOCX_TEXT

    # Verify chunker was called with the right parameters
    mock_text_splitter.assert_called_once_with(
        MOCK_DOCX_TEXT, overlap=settings.SEMCHUNK_OVERLAP_TOKENS
    )
    mock_process_chunks.assert_called_once()
    args, kwargs = mock_process_chunks.call_args
    assert "chunks" in kwargs
    assert "chroma_dir" in kwargs
    assert "document_metadata" in kwargs
    assert kwargs["chroma_dir"] == settings.CHROMA_DIR
    assert kwargs["document_metadata"] == expected_metadata.model_dump()
    assert len(kwargs["chunks"]) == 3

    assert result["document_id"] == expected_metadata.document_id
    assert result["original_filename"] == expected_metadata.original_filename
    assert result["num_chunks"] == 3


@pytest.mark.asyncio
async def test_process_document_no_text(
    test_pdf_file,
    mock_chroma_client,
    mock_openai_client,
    mock_text_splitter,
    mock_process_chunks,
    mock_pdf_loader,
    mock_datastore_service,
):
    """Test processing a document with no content."""
    # Create a mock UploadFile object
    mock_file = Mock(spec=UploadFile)
    mock_file.filename = test_pdf_file.name
    mock_file.content_type = "application/pdf"  # Add MIME type for PDF
    mock_file.seek = AsyncMock()

    # Mock the file.read method to return bytes
    mock_file.read = AsyncMock()
    mock_file.read.return_value = test_pdf_file.read_bytes()

    mock_pdf_loader.return_value = ("", {})
    with pytest.raises(ValueError) as exc_info:
        await process_uploaded_document(mock_file, settings)
    assert "No text extracted from document" in str(exc_info.value)
    mock_text_splitter.split_text.assert_not_called()
    mock_process_chunks.assert_not_called()
    mock_datastore_service.save_document.assert_not_called()


@pytest.mark.asyncio
async def test_process_document_with_error(
    test_pdf_file,
    mock_chroma_client,
    mock_openai_client,
    mock_text_splitter,
    mock_process_chunks,
    mock_pdf_loader,
    mock_datastore_service,
):
    """Test processing a document with an error."""
    # Create a mock UploadFile object
    mock_file = Mock(spec=UploadFile)
    mock_file.filename = test_pdf_file.name
    mock_file.content_type = "application/pdf"  # Add MIME type for PDF
    mock_file.seek = AsyncMock()

    # Mock the file.read method to return bytes
    mock_file.read = AsyncMock()
    mock_file.read.return_value = test_pdf_file.read_bytes()

    mock_text_splitter.side_effect = Exception("Chunking error")
    with pytest.raises(Exception) as exc_info:
        await process_uploaded_document(mock_file, settings)
    assert "Chunking error" in str(exc_info.value)
    mock_text_splitter.split_text.assert_not_called()
    mock_process_chunks.assert_not_called()
    mock_datastore_service.save_document.assert_not_called()
