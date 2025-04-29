"""Integration tests for the document API endpoints."""

import os
import pytest
import shutil
import uuid
from pathlib import Path
from typing import List

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.main import app  # Import your main FastAPI app
from app.services.datastore import DatastoreService, DocumentMetadata
from app.core.config import get_settings, Settings
from tests.fixtures.shared_fixtures import (
    test_settings,
    test_settings_module,
)  # Import both fixtures

# Mark all tests in this module as asyncio
pytestmark = pytest.mark.asyncio


@pytest.fixture(scope="module")
def client(test_settings_module: Settings):
    """Create a TestClient instance for the API tests."""
    # Ensure TESTING environment variable is set for tests to bypass auth
    os.environ["TESTING"] = "true"

    # Override dependency to use test settings
    app.dependency_overrides[get_settings] = lambda: test_settings_module
    yield TestClient(app)
    # Clean up overrides after tests
    app.dependency_overrides = {}
    # Clean up environment variable if needed
    if "TESTING" in os.environ:
        del os.environ["TESTING"]


@pytest.fixture(scope="function")
async def setup_test_documents(test_settings: Settings) -> List[DocumentMetadata]:
    """Set up the datastore with a few test documents for list/delete tests."""
    datastore = DatastoreService(test_settings)
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


async def test_list_documents(
    client: TestClient, setup_test_documents: List[DocumentMetadata]
):
    """Test the GET /api/documents endpoint."""
    response = client.get("/api/documents")
    assert response.status_code == 200
    document_ids = response.json()
    assert isinstance(document_ids, list)
    assert len(document_ids) == len(setup_test_documents)

    expected_ids = {doc.document_id for doc in setup_test_documents}
    assert set(document_ids) == expected_ids


async def test_delete_document_success(
    client: TestClient,
    test_settings: Settings,
    setup_test_documents: List[DocumentMetadata],
):
    """Test the DELETE /api/documents/{document_id} endpoint for successful deletion."""
    datastore = DatastoreService(test_settings)
    doc_to_delete = setup_test_documents[0]
    doc_id_to_delete = doc_to_delete.document_id

    # Verify document exists before deletion
    assert datastore.get_document(doc_id_to_delete) is not None
    assert (datastore.data_dir / doc_id_to_delete).exists()

    # Perform the delete request
    response = client.delete(f"/api/documents/{doc_id_to_delete}")
    assert response.status_code == 204, f"Response content: {response.content}"

    # Verify the document is deleted from datastore
    assert datastore.get_document(doc_id_to_delete) is None
    assert not (datastore.data_dir / doc_id_to_delete).exists()

    # Verify listing shows fewer documents
    response = client.get("/api/documents")
    assert response.status_code == 200
    document_ids = response.json()
    assert doc_id_to_delete not in document_ids
    assert len(document_ids) == len(setup_test_documents) - 1


async def test_delete_document_not_found(client: TestClient):
    """Test deleting a non-existent document ID."""
    non_existent_id = str(uuid.uuid4())
    response = client.delete(f"/api/documents/{non_existent_id}")
    assert response.status_code == 404


async def test_delete_document_invalid_uuid_format(client: TestClient):
    """Test deleting with an invalid UUID format (should still likely be 404)."""
    invalid_id = "not-a-valid-uuid"
    # Depending on implementation, this might be caught by path parameter validation
    # or result in a 404 from the datastore. 404 is acceptable.
    response = client.delete(f"/api/documents/{invalid_id}")
    # FastAPI path validation usually returns 422 for invalid format,
    # but our check happens in the datastore, so 404 is expected.
    assert response.status_code == 404
