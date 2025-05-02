"""Tests for the datastore service."""

import asyncio
import json
import os
import shutil
import tempfile
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import UploadFile

from app.services.datastore import (
    DatastoreService,
    DocumentMetadata,
    get_datastore_service,
)
from app.core.config import Settings, get_settings
from tests.constants import MOCK_PDF_TEXT, MOCK_DOCX_TEXT
from tests.fixtures.shared_fixtures import test_settings  # Import the shared fixture


@pytest.fixture
def datastore_service(test_settings):
    """Create a datastore service with test settings."""
    return DatastoreService(test_settings)


@pytest.fixture
def test_pdf_file():
    """Create a test PDF file."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(b"%PDF-1.4\ntest pdf content")
        pdf_path = f.name

    yield pdf_path

    if os.path.exists(pdf_path):
        os.unlink(pdf_path)


@pytest.fixture
def test_docx_file():
    """Create a test DOCX file."""
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as f:
        f.write(b"PK\x03\x04\x14\x00\x00\x00\x08\x00test docx content")
        docx_path = f.name

    yield docx_path

    if os.path.exists(docx_path):
        os.unlink(docx_path)


@pytest.fixture
def mock_upload_file(test_pdf_file):
    """Create a mock UploadFile."""
    mock_file = MagicMock(spec=UploadFile)
    mock_file.filename = "test_document.pdf"
    mock_file.seek = AsyncMock()

    # Mock the file.read method to return file contents
    with open(test_pdf_file, "rb") as f:
        file_content = f.read()

    mock_file.read = AsyncMock(return_value=file_content)
    return mock_file


@pytest.mark.asyncio
async def test_save_and_retrieve_document(datastore_service, mock_upload_file):
    """Test saving and retrieving a document."""
    # Test data
    test_text_content = MOCK_PDF_TEXT

    # Save the document
    metadata = await datastore_service.save_document(
        mock_upload_file, test_text_content
    )

    # Verify the returned metadata
    assert isinstance(metadata, DocumentMetadata)
    assert metadata.original_filename == mock_upload_file.filename
    assert metadata.document_id is not None
    assert metadata.text_file_path is not None
    assert metadata.original_file_path is not None
    assert metadata.document_dir is not None

    # Verify UUID format for document_id
    document_id = metadata.document_id
    assert isinstance(document_id, str)
    try:
        uuid_obj = uuid.UUID(document_id)
        assert str(uuid_obj) == document_id  # Valid UUID format
    except ValueError:
        pytest.fail(f"document_id {document_id} is not a valid UUID")

    # Retrieve the document metadata
    retrieved_metadata = datastore_service.get_document(document_id)

    # Verify retrieved metadata matches saved metadata
    assert retrieved_metadata is not None
    assert retrieved_metadata.document_id == metadata.document_id
    assert retrieved_metadata.original_filename == metadata.original_filename
    assert retrieved_metadata.original_file_path == metadata.original_file_path
    assert retrieved_metadata.text_file_path == metadata.text_file_path
    assert retrieved_metadata.document_dir == metadata.document_dir

    # Test dictionary-style access
    assert retrieved_metadata["document_id"] == metadata.document_id
    assert retrieved_metadata.get("original_filename") == metadata.original_filename

    # Verify original file exists and has content
    original_file_path = Path(retrieved_metadata.original_file_path)
    assert original_file_path.exists()
    assert original_file_path.stat().st_size > 0

    # Verify text file exists and has content
    text_file_path = Path(retrieved_metadata.text_file_path)
    assert text_file_path.exists()

    # Verify text content was saved correctly
    retrieved_text = datastore_service.get_text_content(document_id)
    assert retrieved_text == test_text_content

    # Test get_original_file_path
    original_path = datastore_service.get_original_file_path(document_id)
    assert original_path is not None
    assert original_path.exists()
    assert original_path.name == mock_upload_file.filename


@pytest.mark.asyncio
async def test_metadata_serialization(datastore_service, mock_upload_file):
    """Test that metadata serialization and deserialization works correctly."""
    # Save document to generate metadata
    metadata = await datastore_service.save_document(mock_upload_file, MOCK_PDF_TEXT)
    document_id = metadata.document_id

    # Verify the metadata.json file exists
    metadata_file = Path(metadata.document_dir) / "metadata.json"
    assert metadata_file.exists()

    # Verify content of metadata file
    with open(metadata_file, "r", encoding="utf-8") as f:
        metadata_dict = json.load(f)

    assert metadata_dict["document_id"] == metadata.document_id
    assert metadata_dict["original_filename"] == metadata.original_filename

    # Test re-loading the metadata
    with open(metadata_file, "w", encoding="utf-8") as f:
        # Add a test field to see if it gets preserved
        metadata_dict["test_field"] = "test_value"
        json.dump(metadata_dict, f, indent=2)

    # Retrieve the modified metadata
    retrieved_metadata = datastore_service.get_document(document_id)

    # Pydantic should ignore the extra field by default
    assert not hasattr(retrieved_metadata, "test_field")


def test_datastore_directory_creation(test_settings):
    """Test that the datastore directory is created if it doesn't exist."""
    # Remove the data directory if it exists
    if test_settings.DATA_DIR.exists():
        shutil.rmtree(test_settings.DATA_DIR)

    # Create a new datastore service, which should create the directory
    service = DatastoreService(test_settings)

    # Verify the directory was created
    assert test_settings.DATA_DIR.exists()
    assert test_settings.DATA_DIR.is_dir()


def test_nonexistent_document(datastore_service):
    """Test behavior when retrieving a nonexistent document."""
    # Generate a random UUID that shouldn't exist
    nonexistent_id = str(uuid.uuid4())

    # Verify get_document returns None
    assert datastore_service.get_document(nonexistent_id) is None

    # Verify get_original_file_path returns None
    assert datastore_service.get_original_file_path(nonexistent_id) is None

    # Verify get_text_content returns None
    assert datastore_service.get_text_content(nonexistent_id) is None


def test_get_datastore_service_function():
    """Test that get_datastore_service returns a DatastoreService instance."""
    settings = get_settings()
    service = get_datastore_service(settings)
    assert isinstance(service, DatastoreService)
