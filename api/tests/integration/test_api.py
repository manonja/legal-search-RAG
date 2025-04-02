"""Integration tests for the FastAPI endpoints."""

import asyncio
import os
import shutil
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.core.config import get_settings
from app.main import app
from app.services.database.chroma import get_collection
from app.services.documents.query import process_query
from app.services.documents.search import search_documents

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
def test_client() -> Generator:
    """Create a test client for the FastAPI app."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
async def async_client() -> AsyncGenerator:
    """Create an async test client for the FastAPI app."""
    async with AsyncClient(app=app, base_url="http://test") as client:
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
def mock_create_text_splitter(mocker):
    """Mock the text splitter creation function."""
    mock_splitter = mocker.MagicMock()
    mock_splitter.split_text.return_value = [
        "This is chunk 1",
        "This is chunk 2",
        "This is chunk 3",
    ]
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
def mock_chroma_client(mocker):
    """Mock the ChromaDB client."""
    # Create a mock collection
    mock_collection = MagicMock()
    mock_collection.add = MagicMock()

    # Create a mock client
    mock_client = MagicMock()
    mock_client.get_or_create_collection.return_value = mock_collection

    # Patch the PersistentClient in the embeddings module
    # This is what process_chunks uses internally
    mocker.patch(
        "app.services.embeddings.chromadb.PersistentClient", return_value=mock_client
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
    mock_create_text_splitter,
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
    assert response_json["chunks"] == 3, (
        "Should have 3 chunks from mock_create_text_splitter"
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

    # Verify text splitting
    mock_create_text_splitter.assert_called_once()
    splitter_instance = mock_create_text_splitter.return_value
    splitter_instance.split_text.assert_called_once()

    # Verify that process_chunks was called
    mock_process_chunks.assert_called_once()

    # Verify process_chunks arguments
    args = mock_process_chunks.call_args[0]
    # Verify the first argument is a Path to a file with the expected name
    assert isinstance(args[0], Path), (
        "First argument to process_chunks should be a Path"
    )
    assert args[0].name.endswith(f"chunked_sample.pdf.txt"), (
        f"Expected chunked filename, got {args[0].name}"
    )


def test_upload_document_docx(
    test_client: TestClient,
    mock_extract_pdf_text,
    mock_extract_docx_text,
    mock_create_text_splitter,
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
        assert response_json["chunks"] == 3, (
            "Should have 3 chunks from mock_create_text_splitter"
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

        # Verify text splitting
        mock_create_text_splitter.assert_called_once()
        splitter_instance = mock_create_text_splitter.return_value
        splitter_instance.split_text.assert_called_once()

        # Verify that process_chunks was called
        mock_process_chunks.assert_called_once()

        # Verify process_chunks arguments
        args = mock_process_chunks.call_args[0]
        # Verify the first argument is a Path to a file with the expected name
        assert isinstance(args[0], Path), (
            "First argument to process_chunks should be a Path"
        )
        assert args[0].name.endswith(f"chunked_test_document.docx.txt"), (
            f"Expected chunked filename, got {args[0].name}"
        )

    finally:
        os.unlink(docx_path)


def test_get_document(
    test_client: TestClient,
    test_pdf_document: Path,
    mock_extract_pdf_text,
    mock_create_text_splitter,
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
