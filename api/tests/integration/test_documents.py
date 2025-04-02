"""Integration tests for document operations."""

import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tests.constants import MOCK_PDF_TEXT, MOCK_DOCX_TEXT
from tests.fixtures.document_fixtures import mock_datastore_service  # Import fixture


@pytest.mark.parametrize(
    "file_type,file_content,mime_type,expected_text,filename",
    [
        (
            "pdf",
            None,  # Use the fixture test_pdf_document
            "application/pdf",
            MOCK_PDF_TEXT,
            "sample.pdf",
        ),
        (
            "docx",
            b"PK\x03\x04\x14\x00\x00\x00\x08\x00",  # Minimal DOCX header
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            MOCK_DOCX_TEXT,
            "test_document.docx",
        ),
    ],
)
def test_upload_document(
    test_client,
    file_type,
    file_content,
    mime_type,
    filename,
    mock_extract_pdf_text,
    mock_extract_docx_text,
    mock_create_text_splitter,
    mock_process_chunks,
    mock_datastore_service,
    test_pdf_document,
):
    """Test document upload with different file types."""
    # Setup file for upload
    if file_type == "pdf":
        file_path = test_pdf_document
    else:
        with tempfile.NamedTemporaryFile(suffix=f".{file_type}", delete=False) as f:
            f.write(file_content)
            file_path = f.name

    try:
        # Upload file
        with open(file_path, "rb") as f:
            files = {"file": (filename, f, mime_type)}
            response = test_client.post("/api/documents/upload", files=files)

        # Check response
        assert response.status_code == 200  # noqa: S101
        response_json = response.json()

        # Validate proper fields exist
        assert "document_id" in response_json, "Response missing 'document_id' field"
        assert "original_filename" in response_json, (
            "Response missing 'original_filename' field"
        )
        assert "chunks" in response_json, "Response missing 'chunks' field"
        assert "status" in response_json, "Response missing 'status' field"
        assert "message" in response_json, "Response missing 'message' field"

        # Validate response values
        assert response_json["original_filename"] == filename, (
            "Original filename should be preserved"
        )
        assert response_json["chunks"] == 3, "Should have 3 chunks"
        assert response_json["status"] == "success", "Status should be 'success'"
        assert response_json["message"] == "Document processed successfully", (
            "Message should indicate success"
        )

        # Validate UUID format
        document_id = response_json["document_id"]
        assert isinstance(document_id, str), "document_id should be a string"
        assert len(document_id) > 0, "document_id should not be empty"

        # Just verify the datastore service was called
        mock_datastore_service.save_document.assert_called_once()

        # Verify appropriate extraction method was called
        if file_type == "pdf":
            mock_extract_pdf_text.assert_called_once()
            assert mock_extract_docx_text.call_count == 0, (
                "DOCX extraction should not be called for PDF files"
            )
        else:
            assert mock_extract_pdf_text.call_count == 0, (
                "PDF extraction should not be called for DOCX files"
            )
            mock_extract_docx_text.assert_called_once()

        # Verify text splitting
        mock_create_text_splitter.assert_called_once()
        splitter_instance = mock_create_text_splitter.return_value
        splitter_instance.split_text.assert_called_once()

        # Verify chunk processing
        mock_process_chunks.assert_called_once()
        args = mock_process_chunks.call_args[0]
        assert args[0].name.endswith(f"chunked_{filename}.txt"), (
            f"Expected chunked filename, got {args[0].name}"
        )

    finally:
        if file_type != "pdf":
            os.unlink(file_path)


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
    assert document_id, "Response should include a document_id"
    assert isinstance(document_id, str), "document_id should be a string"
    assert len(document_id) > 0, "document_id should not be empty"

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
