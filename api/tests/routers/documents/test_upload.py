"""Tests for document upload router."""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import shutil
import os

from app.main import app
from app.core.config import get_settings

# Get settings
settings = get_settings()

# Create test client
client = TestClient(app)


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


def test_upload_document():
    """Test document upload endpoint."""
    # Create a test PDF file
    test_file = Path(settings.DOCS_ROOT) / "test.pdf"
    test_file.write_text("Test content")

    # Upload the file
    with open(test_file, "rb") as f:
        response = client.post(
            "/documents/upload", files={"file": ("test.pdf", f, "application/pdf")}
        )

    # Check response
    pytest.assume(response.status_code == 200)
    data = response.json()
    pytest.assume(data["status"] == "success")
    pytest.assume("document_id" in data)
    pytest.assume(data["chunks"] > 0)


def test_upload_invalid_file():
    """Test upload with invalid file type."""
    # Create a test file with invalid extension
    test_file = Path(settings.DOCS_ROOT) / "test.txt"
    test_file.write_text("Test content")

    # Try to upload the file
    with open(test_file, "rb") as f:
        response = client.post(
            "/documents/upload", files={"file": ("test.txt", f, "text/plain")}
        )

    # Check response
    pytest.assume(response.status_code == 400)
    data = response.json()
    pytest.assume("detail" in data)
    pytest.assume("Unsupported file type" in data["detail"])
