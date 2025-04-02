"""Configure pytest environment and provide common fixtures."""

import os
import sys
import shutil
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient
from unittest.mock import MagicMock

from app.main import app
from app.core.config import get_settings
from tests.constants import (
    TEST_DOCUMENT_ID,
    TEST_DOCUMENT_CONTENT,
    MOCK_SEARCH_RESULT_TEXT,
    MOCK_OPENAI_RESPONSE,
    PDF_SAMPLE_PATH,
)

# Add the project root directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set testing environment variable
os.environ["TESTING"] = "true"

# Explicitly disable Sentry for tests
os.environ["SENTRY_DSN"] = ""

# Disable Sentry client if it's initialized
try:
    import sentry_sdk

    # Initialize with empty DSN to disable
    sentry_sdk.init(dsn="")
except ImportError as e:
    # Log using print since logger might not be configured yet
    print(f"Sentry SDK not installed, no need to disable: {e}")
except Exception as e:
    print(f"Error while disabling Sentry SDK: {e}")

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
    doc_path = Path(PDF_SAMPLE_PATH)
    yield doc_path


@pytest.fixture
def mock_chroma_collection(mocker):
    """Mock the ChromaDB collection."""
    mock_collection = MagicMock()
    mock_collection.query.return_value = {
        "documents": [[MOCK_SEARCH_RESULT_TEXT]],
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
        choices=[MagicMock(message=MagicMock(content=MOCK_OPENAI_RESPONSE))]
    )
    mocker.patch(
        "app.services.documents.query.get_openai_client", return_value=mock_client
    )
    return mock_client


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


# Import document fixtures for global availability
from tests.fixtures.document_fixtures import (
    mock_extract_pdf_text,
    mock_extract_docx_text,
    mock_create_text_splitter,
    mock_process_chunks,
    mock_document_service,
    mock_document_not_found,
    mock_process_uploaded_document,
)


@pytest.fixture(autouse=True)
def disable_sentry():
    """Disable Sentry SDK for all tests."""
    try:
        import sentry_sdk

        # Initialize with an empty DSN to disable Sentry
        sentry_sdk.init(dsn="")

        yield

    except ImportError as e:
        # Sentry not installed, nothing to do
        print(f"Sentry SDK not available, skipping disable: {e}")
        yield
    except Exception as e:
        print(f"Error in disable_sentry fixture: {e}")
        yield
