import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile
import shutil
from app.main import app
from app.services.documents.document import get_document_content

client = TestClient(app)


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
def test_document_file(test_dir, sample_document_content):
    """Create a test document file."""
    doc_path = test_dir / "test_doc.txt"
    doc_path.write_text(sample_document_content)
    return doc_path


@pytest.fixture
def mock_get_document_content(mocker):
    """Mock the get_document_content function."""
    mock_get = mocker.MagicMock(
        return_value=("Test document content", {"title": "Test Document"})
    )
    mocker.patch(
        "app.routers.documents.document.get_document_content", return_value=mock_get
    )
    return mock_get


def test_get_document_success(test_document_file, mock_get_document_content):
    """Test successfully retrieving a document."""
    response = client.get(f"/documents/{test_document_file.name}")
    assert response.status_code == 200
    assert response.json()["content"] == "Test document content"
    assert response.json()["metadata"]["title"] == "Test Document"
    mock_get_document_content.assert_called_once()


def test_get_document_not_found(mock_get_document_content):
    """Test retrieving a non-existent document."""
    mock_get_document_content.side_effect = FileNotFoundError("Document not found")
    response = client.get("/documents/nonexistent.txt")
    assert response.status_code == 404
    assert "Document not found" in response.json()["detail"]
    mock_get_document_content.assert_called_once()


def test_get_document_error(mock_get_document_content):
    """Test retrieving a document with an error."""
    mock_get_document_content.side_effect = IOError("Error reading document")
    response = client.get("/documents/test.txt")
    assert response.status_code == 500
    assert "Error reading document" in response.json()["detail"]
    mock_get_document_content.assert_called_once()


def test_get_document_invalid_id(mock_get_document_content):
    """Test retrieving a document with an invalid ID."""
    mock_get_document_content.side_effect = ValueError("Invalid document ID")
    response = client.get("/documents/invalid_id")
    assert response.status_code == 500
    assert "Invalid document ID" in response.json()["detail"]
    mock_get_document_content.assert_called_once()
