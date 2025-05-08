"""Document-related fixtures for tests."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from pathlib import Path
import uuid

from tests.constants import MOCK_PDF_TEXT, MOCK_DOCX_TEXT, MOCK_DOCUMENT_CHUNKS


@pytest.fixture
def mock_extract_pdf_text(mocker):
    """Mock PDF text extraction.

    DEPRECATED: Use mock_pdf_loader instead.
    """
    mock_extract = mocker.MagicMock(return_value="Mocked PDF text")
    mocker.patch("app.services.documents.upload.extract_pdf_text", new=mock_extract)
    return mock_extract


@pytest.fixture
def mock_extract_docx_text(mocker):
    """Mock DOCX text extraction.

    DEPRECATED: Use mock_docx_loader instead.
    """
    mock_extract = mocker.MagicMock(return_value="Mocked DOCX text")
    mocker.patch("app.services.documents.upload.extract_docx_text", new=mock_extract)
    return mock_extract


@pytest.fixture
def mock_pdf_loader(mocker):
    """Mock PDF loader."""
    mock_load = mocker.MagicMock(return_value=("Mocked PDF text", {}))
    mock_loader = mocker.MagicMock()
    mock_loader.load = mock_load
    mocker.patch(
        "app.services.documents.upload.PDFLoader",
        return_value=mock_loader,
    )
    return mock_load


@pytest.fixture
def mock_docx_loader(mocker):
    """Mock DOCX loader."""
    mock_load = mocker.MagicMock(return_value=("Mocked DOCX text", {}))
    mock_loader = mocker.MagicMock()
    mock_loader.load = mock_load
    mocker.patch(
        "app.services.documents.upload.DOCXLoader",
        return_value=mock_loader,
    )
    return mock_load


# Fixture is no longer needed as create_text_splitter was removed
# @pytest.fixture
# def mock_create_text_splitter(mocker):
#     """Mock the text splitter creation function."""
#     mock_splitter = mocker.MagicMock()
#     mock_splitter.split_text.return_value = MOCK_DOCUMENT_CHUNKS
#     mock_create = mocker.MagicMock(return_value=mock_splitter)
#     mocker.patch("app.services.documents.upload.create_text_splitter", new=mock_create)
#     return mock_create # Return the mock create function itself


@pytest.fixture
def mock_process_chunks(mocker):
    """Mock the chunk processing function."""
    mock_process = mocker.MagicMock()
    mocker.patch("app.services.documents.upload.process_chunks", new=mock_process)
    return mock_process


@pytest.fixture
def mock_process_uploaded_document(mocker):
    """Mock the document processing function."""
    test_uuid = str(uuid.uuid4())
    mock_process = mocker.AsyncMock(
        return_value={
            "document_id": test_uuid,
            "original_filename": "test_document.pdf",
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


@pytest.fixture
def mock_datastore_service(mocker):
    """Mock the datastore service."""
    test_uuid = str(uuid.uuid4())

    # Create a dynamic mock that uses the actual filename from the UploadFile argument
    async def mock_save_document(file, text_content=""):
        # Get the original filename from the file argument
        original_filename = (
            file.filename if hasattr(file, "filename") else "test_document.pdf"
        )

        # Create mock DocumentMetadata
        mock_metadata = mocker.MagicMock()
        mock_metadata.document_id = test_uuid
        mock_metadata.original_filename = original_filename
        mock_metadata.original_file_path = f"/data/{test_uuid}/{original_filename}"
        mock_metadata.text_file_path = f"/data/{test_uuid}/extracted_text.txt"
        mock_metadata.document_dir = f"/data/{test_uuid}"

        # Support dictionary-style access
        mock_metadata.__getitem__.side_effect = lambda key: getattr(mock_metadata, key)
        mock_metadata.get.side_effect = lambda key, default=None: getattr(
            mock_metadata, key, default
        )
        mock_metadata.model_dump.return_value = {
            "document_id": test_uuid,
            "original_filename": original_filename,
            "original_file_path": f"/data/{test_uuid}/{original_filename}",
            "text_file_path": f"/data/{test_uuid}/extracted_text.txt",
            "document_dir": f"/data/{test_uuid}",
        }

        return mock_metadata

    # Create mock datastore service
    mock_datastore = mocker.MagicMock()
    mock_datastore.save_document = AsyncMock(side_effect=mock_save_document)

    # Patch the service
    mocker.patch(
        "app.services.documents.upload.get_datastore_service",
        return_value=mock_datastore,
    )

    return mock_datastore
