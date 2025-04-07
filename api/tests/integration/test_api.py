"""Integration tests for the FastAPI endpoints."""

import os
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import AsyncGenerator, Generator, List
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.core.config import get_settings
from app.main import app
from app.services.datastore import DatastoreService, DocumentMetadata
from tests.constants import MOCK_PDF_TEXT, MOCK_DOCX_TEXT  # Import constants
from tests.conftest_auth import mock_api_token  # Import auth test fixture
from tests.services.test_datastore import test_settings  # Import test_settings fixture

# Set testing environment variable
os.environ["TESTING"] = "true"

# Get settings
settings = get_settings()

# Test data
TEST_QUERY = "What are the legal requirements for contracts?"
TEST_DOCUMENT_ID = "test_document.txt"
TEST_DOCUMENT_CONTENT = "This is a test document for integration testing."
TEST_UUID = "test-uuid-12345-67890"


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
def test_client() -> Generator:
    """Create a test client for the FastAPI app."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def document_test_client(monkeypatch) -> Generator:
    """Create a test client specifically for document API tests.

    This fixture creates a test app with the document router properly configured
    with its dependencies to test document endpoints directly, and auth bypassed.
    """
    from fastapi import FastAPI, Depends, Request
    from app.routers.documents.document import router as document_router
    from app.services.datastore import DatastoreService, get_datastore_service
    from app.core.config import get_settings

    # Create a test app with only the document router
    test_app = FastAPI()

    # Get settings for the test
    settings = get_settings()

    # Disable auth for testing by overriding the auth dependency
    # This allows us to test the routes without authentication
    async def skip_auth():
        return True

    # Register the router without auth dependency
    # We need to clone the router to avoid modifying the original
    from fastapi import APIRouter
    from app.routers.documents.document import router as original_router

    test_router = APIRouter()
    for route in original_router.routes:
        test_router.routes.append(route)

    # Clear dependencies if any
    test_router.dependencies = []

    # Mount the router
    test_app.include_router(test_router)

    # Create a properly configured test client
    with TestClient(test_app) as client:
        yield client


@pytest.fixture
async def async_client() -> AsyncGenerator:
    """Create an async test client for the FastAPI app."""
    async with AsyncClient(base_url="http://test") as client:
        yield client


@pytest.fixture
def test_document(tmp_path: Path) -> Generator:
    """Create a test document for testing document retrieval."""
    doc_path = tmp_path / TEST_DOCUMENT_ID
    doc_path.write_text(TEST_DOCUMENT_CONTENT)
    yield doc_path
    doc_path.unlink(missing_ok=True)


@pytest.fixture
def test_pdf_document() -> Generator:
    """Create a test PDF document for testing document upload."""
    doc_path = Path("tests/fixtures/sample.pdf")
    yield doc_path


@pytest.fixture
def mock_process_uploaded_document(mocker):
    """Mock the document processing function."""
    mock_process = mocker.AsyncMock(
        return_value={
            "document_id": TEST_UUID,
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
def mock_chroma_collection(mocker):
    """Mock the ChromaDB collection."""
    mock_collection = MagicMock()
    mock_collection.query.return_value = {
        "documents": [["This is a relevant document chunk about contracts."]],
        "metadatas": [[{"source": "test_doc.pdf", "page": 1}]],
        "distances": [[0.5]],
    }
    mocker.patch(
        "app.services.documents.search.get_collection", return_value=mock_collection
    )
    return mock_collection


@pytest.fixture
def mock_openai_client(mocker):
    """Mock the OpenAI client."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(
                    content="This is a generated response about contracts."
                )
            )
        ]
    )
    mocker.patch(
        "app.services.documents.query.get_openai_client", return_value=mock_client
    )
    return mock_client


@pytest.fixture
def mock_extract_pdf_text(mocker):
    """Mock the PDF text extraction function."""
    mock_extract = mocker.MagicMock(
        return_value="This is extracted text from the PDF document. It contains multiple paragraphs that will be split into chunks."
    )
    mocker.patch("app.services.documents.upload.extract_pdf_text", new=mock_extract)
    return mock_extract


@pytest.fixture
def mock_extract_docx_text(mocker):
    """Mock the DOCX text extraction function."""
    mock_extract = mocker.MagicMock(
        return_value="This is extracted text from the DOCX document."
    )
    mocker.patch("app.services.documents.upload.extract_docx_text", new=mock_extract)
    return mock_extract


@pytest.fixture
def mock_process_chunks(mocker):
    """Mock the chunk processing function."""
    mock_process = mocker.MagicMock()
    mocker.patch("app.services.documents.upload.process_chunks", new=mock_process)
    return mock_process


@pytest.fixture
def mock_chroma_client(mocker):
    """Mock the ChromaDB client."""
    # Create a mock collection
    mock_collection = MagicMock()
    mock_collection.add = MagicMock()

    # Create a mock client
    mock_client = MagicMock()
    mock_client.get_or_create_collection.return_value = mock_collection

    # Patch the PersistentClient in the correct location
    mocker.patch(
        "app.services.database.chroma.chromadb.PersistentClient",
        return_value=mock_client,
    )

    return mock_client


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


# Import mock_datastore_service from fixtures
from tests.fixtures.document_fixtures import mock_datastore_service


@pytest.fixture(scope="function")
async def setup_test_documents(settings=None) -> List[DocumentMetadata]:
    """Set up the datastore with a few test documents for list/delete tests."""
    # Use the app settings if no settings provided
    if settings is None:
        settings = get_settings()

    datastore = DatastoreService(settings)
    doc_metadatas = []

    # Create dummy files and save them using datastore
    for i in range(3):
        filename = f"test_doc_{i}.txt"
        doc_id = str(uuid.uuid4())
        doc_dir = datastore.data_dir / doc_id
        doc_dir.mkdir(parents=True, exist_ok=True)

        # Create dummy original file
        original_file_path = doc_dir / filename
        with open(original_file_path, "w") as f:
            f.write(f"Content of {filename}")

        # Create dummy text file
        text_file_path = doc_dir / "extracted_text.txt"
        with open(text_file_path, "w") as f:
            f.write(f"Extracted text for {filename}")

        # Create metadata object
        metadata = DocumentMetadata(
            document_id=doc_id,
            original_filename=filename,
            original_file_path=str(original_file_path),
            text_file_path=str(text_file_path),
            document_dir=str(doc_dir),
        )
        doc_metadatas.append(metadata)

        # Save metadata file
        with open(doc_dir / "metadata.json", "w") as f:
            f.write(metadata.model_dump_json(indent=2))

    yield doc_metadatas

    # Teardown: Clean up the test documents (test_settings fixture handles the root dir)
    # No explicit cleanup needed here as test_settings fixture cleans the whole temp dir


def test_health_check(test_client: TestClient) -> None:
    """Test the health check endpoint."""
    response = test_client.get("/api/health")
    assert response.status_code == 200  # noqa: S101


def test_search_documents(test_client: TestClient, mock_chroma_collection) -> None:
    """Test the search documents endpoint."""
    response = test_client.post("/api/search", json={"query": TEST_QUERY, "limit": 5})
    assert response.status_code == 200  # noqa: S101
    assert len(response.json()) > 0
    assert "text" in response.json()[0]
    assert "metadata" in response.json()[0]
    assert "distance" in response.json()[0]
    assert (
        response.json()[0]["text"]
        == "This is a relevant document chunk about contracts."
    )
    assert response.json()[0]["metadata"]["source"] == "test_doc.pdf"
    assert response.json()[0]["distance"] == 0.5


def test_legacy_search_documents(
    test_client: TestClient, mock_chroma_collection
) -> None:
    """Test the legacy search documents endpoint."""
    response = test_client.post(
        "/api/search/api",
        json={
            "query_text": TEST_QUERY,
            "n_results": 3,
            "min_similarity": 0.7,
            "metadata_filter": None,
        },
    )
    assert response.status_code == 200  # noqa: S101
    assert "results" in response.json()
    assert "total_found" in response.json()
    assert len(response.json()["results"]) > 0
    assert (
        response.json()["results"][0]["text"]
        == "This is a relevant document chunk about contracts."
    )
    assert response.json()["results"][0]["metadata"]["source"] == "test_doc.pdf"
    assert response.json()["results"][0]["distance"] == 0.5


def test_rag_search(
    test_client: TestClient, mock_chroma_collection, mock_openai_client
) -> None:
    """Test the RAG search endpoint."""
    response = test_client.post(
        "/api/rag-search",
        json={
            "query": TEST_QUERY,
            "max_results": 5,
            "temperature": 0.7,
            "max_tokens": 1000,
        },
    )
    assert response.status_code == 200  # noqa: S101
    assert "answer" in response.json()
    assert "sources" in response.json()
    assert "confidence" in response.json()
    assert isinstance(response.json()["sources"], list)
    assert isinstance(response.json()["confidence"], float)


def test_upload_document(
    test_client: TestClient,
    test_pdf_document: Path,
    mock_extract_pdf_text,
    mock_extract_docx_text,
    mock_process_chunks,
    mock_chroma_client,
    mock_datastore_service,
) -> None:
    """Test document upload endpoint."""
    with open(test_pdf_document, "rb") as f:
        files = {"file": ("sample.pdf", f, "application/pdf")}
        response = test_client.post("/api/documents/upload", files=files)

    # Validate the HTTP response
    assert response.status_code == 200  # noqa: S101

    # Validate the response JSON structure
    response_json = response.json()
    assert isinstance(response_json, dict), "Response should be a JSON object"

    # Validate that we get a UUID and the original filename is preserved
    assert "document_id" in response_json, "Response missing 'document_id' field"
    assert "original_filename" in response_json, (
        "Response missing 'original_filename' field"
    )
    assert "chunks" in response_json, "Response missing 'chunks' field"
    assert "status" in response_json, "Response missing 'status' field"
    assert "message" in response_json, "Response missing 'message' field"

    # Validate response values
    assert response_json["original_filename"] == "sample.pdf", (
        "Original filename should be preserved"
    )
    assert response_json["chunks"] == 1, (
        "Should have 1 chunk for the short mock text with semchunk"
    )
    assert response_json["status"] == "success", "Status should be 'success'"
    assert response_json["message"] == "Document processed successfully", (
        "Message should indicate success"
    )

    # Validate UUID format (should be a string with proper UUID structure)
    document_id = response_json["document_id"]
    assert isinstance(document_id, str), "document_id should be a string"
    assert len(document_id) > 0, "document_id should not be empty"

    # In this test, we're using real implementation with mocks, so we can't directly compare UUIDs
    # Just verify that mock_datastore_service.save_document was called
    mock_datastore_service.save_document.assert_called_once()

    # Verify the processing pipeline
    mock_extract_pdf_text.assert_called_once()

    # Check that docx extraction was not called
    assert mock_extract_docx_text.call_count == 0, (
        "DOCX extraction should not be called for PDF files"
    )

    # Verify that process_chunks was called
    mock_process_chunks.assert_called_once()

    # Verify process_chunks arguments using kwargs
    assert mock_process_chunks.call_args is not None, "process_chunks was not called"
    kwargs = mock_process_chunks.call_args.kwargs  # Access keyword args
    assert "chunks" in kwargs, "chunks list missing in process_chunks kwargs"
    assert isinstance(kwargs["chunks"], list), "chunks argument should be a list"
    assert "document_metadata" in kwargs, (
        "document_metadata missing in process_chunks kwargs"
    )
    assert isinstance(kwargs["document_metadata"], dict), (
        "document_metadata should be a dict"
    )
    # Optionally add more specific checks on metadata content if needed:
    # assert kwargs["document_metadata"]["document_id"] == document_id
    # assert kwargs["document_metadata"]["original_filename"] == "sample.pdf"


def test_upload_document_docx(
    test_client: TestClient,
    mock_extract_pdf_text,
    mock_extract_docx_text,
    mock_process_chunks,
    mock_chroma_client,
    mock_datastore_service,
) -> None:
    """Test document upload endpoint with DOCX file."""
    # Create a test DOCX file
    docx_content = b"PK\x03\x04\x14\x00\x00\x00\x08\x00"  # Minimal DOCX header
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
        f.write(docx_content)
        docx_path = f.name

    try:
        with open(docx_path, "rb") as f:
            files = {
                "file": (
                    "test_document.docx",
                    f,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            }
            response = test_client.post("/api/documents/upload", files=files)

        # Validate the HTTP response
        assert response.status_code == 200  # noqa: S101

        # Validate the response JSON structure
        response_json = response.json()
        assert isinstance(response_json, dict), "Response should be a JSON object"

        # Validate that we get a UUID and the original filename is preserved
        assert "document_id" in response_json, "Response missing 'document_id' field"
        assert "original_filename" in response_json, (
            "Response missing 'original_filename' field"
        )
        assert "chunks" in response_json, "Response missing 'chunks' field"
        assert "status" in response_json, "Response missing 'status' field"
        assert "message" in response_json, "Response missing 'message' field"

        # Validate response values
        assert response_json["original_filename"] == "test_document.docx", (
            "Original filename should be preserved"
        )
        assert response_json["chunks"] == 1, (
            "Should have 1 chunk for the short mock text with semchunk"
        )
        assert response_json["status"] == "success", "Status should be 'success'"
        assert response_json["message"] == "Document processed successfully", (
            "Message should indicate success"
        )

        # Validate UUID format (should be a string with proper UUID structure)
        document_id = response_json["document_id"]
        assert isinstance(document_id, str), "document_id should be a string"
        assert len(document_id) > 0, "document_id should not be empty"

        # In this test, we're using real implementation with mocks, so we can't directly compare UUIDs
        # Just verify that mock_datastore_service.save_document was called
        mock_datastore_service.save_document.assert_called_once()

        # Verify the processing pipeline
        assert mock_extract_pdf_text.call_count == 0, (
            "PDF extraction should not be called for DOCX files"
        )
        mock_extract_docx_text.assert_called_once()

        # Verify that process_chunks was called
        mock_process_chunks.assert_called_once()

        # Verify process_chunks arguments using kwargs
        assert mock_process_chunks.call_args is not None, (
            "process_chunks was not called"
        )
        kwargs = mock_process_chunks.call_args.kwargs  # Access keyword args
        assert "chunks" in kwargs, "chunks list missing in process_chunks kwargs"
        assert isinstance(kwargs["chunks"], list), "chunks argument should be a list"
        assert "document_metadata" in kwargs, (
            "document_metadata missing in process_chunks kwargs"
        )
        assert isinstance(kwargs["document_metadata"], dict), (
            "document_metadata should be a dict"
        )
        # Optionally add more specific checks on metadata content if needed:
        # assert kwargs["document_metadata"]["document_id"] == document_id
        # assert kwargs["document_metadata"]["original_filename"] == "test_document.docx"

    finally:
        os.unlink(docx_path)


def test_get_document(
    test_client: TestClient,
    test_pdf_document: Path,
    mock_extract_pdf_text,
    mock_process_chunks,
    mock_chroma_client,
    mock_document_service,
    mock_datastore_service,
) -> None:
    """Test the document retrieval endpoint."""
    # First upload the document
    with open(test_pdf_document, "rb") as f:
        files = {"file": ("sample.pdf", f, "application/pdf")}
        upload_response = test_client.post("/api/documents/upload", files=files)

    assert upload_response.status_code == 200  # noqa: S101
    document_id = upload_response.json()["document_id"]
    assert document_id  # Should be a non-empty UUID

    # Then retrieve it
    response = test_client.get(f"/api/documents/{document_id}")
    assert response.status_code == 200  # noqa: S101

    # Verify response content
    response_json = response.json()
    assert response_json["content"] == mock_document_service["content"]
    assert response_json["metadata"] == mock_document_service["metadata"]
    assert "source" in response_json
    assert isinstance(response_json["chunks"], list)


def test_get_document_not_found(
    test_client: TestClient, mock_document_not_found
) -> None:
    """Test document retrieval with non-existent document."""
    response = test_client.get("/api/documents/nonexistent.txt")
    assert response.status_code == 404  # noqa: S101
    assert "Document not found" in response.json()["detail"]  # noqa: S101


def test_cors_middleware(test_client: TestClient) -> None:
    """Test CORS middleware is properly configured."""
    response = test_client.options(
        "/api/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200  # noqa: S101
    # FastAPI returns the specific origin instead of '*' when allow_credentials=True
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"  # noqa: S101
    assert "access-control-allow-credentials" in response.headers  # noqa: S101
    assert response.headers["access-control-allow-credentials"] == "true"  # noqa: S101


async def test_list_documents(setup_test_documents: List[DocumentMetadata]):
    """Test listing documents directly through the service layer instead of HTTP."""
    # Get datastore service instance
    settings = get_settings()
    datastore = DatastoreService(settings)

    # Call the service method directly
    document_ids = datastore.list_document_ids()

    # Verify the results
    assert isinstance(document_ids, list)
    assert len(document_ids) >= len(setup_test_documents)

    # Check that all our test document IDs are in the returned list
    expected_ids = {doc.document_id for doc in setup_test_documents}
    assert expected_ids.issubset(set(document_ids))


async def test_delete_document_success(setup_test_documents: List[DocumentMetadata]):
    """Test document deletion directly through the service layer instead of HTTP."""
    # Get datastore service
    settings = get_settings()
    datastore = DatastoreService(settings)

    # Get a document to delete
    doc_to_delete = setup_test_documents[0]
    doc_id_to_delete = doc_to_delete.document_id

    # Verify document exists before deletion
    assert datastore.get_document(doc_id_to_delete) is not None
    assert (datastore.data_dir / doc_id_to_delete).exists()

    # Delete the document directly through the service
    result = datastore.delete_document(doc_id_to_delete)
    assert result is True

    # Verify the document is deleted
    assert datastore.get_document(doc_id_to_delete) is None
    assert not (datastore.data_dir / doc_id_to_delete).exists()

    # Verify document isn't in the list anymore
    document_ids = datastore.list_document_ids()
    assert doc_id_to_delete not in document_ids


async def test_delete_document_not_found():
    """Test deleting a non-existent document directly through the service layer."""
    # Get datastore service
    settings = get_settings()
    datastore = DatastoreService(settings)

    # Generate a UUID that shouldn't exist
    non_existent_id = str(uuid.uuid4())

    # Try to delete a non-existent document
    result = datastore.delete_document(non_existent_id)

    # Service should return False for non-existent document
    assert result is False


async def test_delete_document_invalid_uuid_format():
    """Test deleting with an invalid UUID format directly through the service layer."""
    # Get datastore service
    settings = get_settings()
    datastore = DatastoreService(settings)

    # Try an invalid UUID format
    invalid_id = "not-a-valid-uuid"

    # The service should handle this gracefully
    result = datastore.delete_document(invalid_id)

    # Service should return False for invalid UUID
    assert result is False
