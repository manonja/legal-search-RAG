"""Integration tests for document operations."""

import os
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tests.constants import MOCK_PDF_TEXT, MOCK_DOCX_TEXT


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
    expected_text,
    filename,
    mock_extract_pdf_text,
    mock_extract_docx_text,
    mock_create_text_splitter,
    mock_process_chunks,
    mock_chroma_client,
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
        assert response_json["document_id"] == filename
        assert response_json["chunks"] == 3
        assert response_json["status"] == "success"
        assert response_json["message"] == "Document processed successfully"

        # Verify appropriate extraction method was called
        if file_type == "pdf":
            mock_extract_pdf_text.assert_called_once()
            mock_extract_docx_text.assert_not_called()
        else:
            mock_extract_pdf_text.assert_not_called()
            mock_extract_docx_text.assert_called_once()

        # Verify text splitting
        mock_create_text_splitter.assert_called_once()
        splitter_instance = mock_create_text_splitter.return_value
        splitter_instance.split_text.assert_called_once_with(expected_text)

        # Verify chunk processing
        mock_process_chunks.assert_called_once()
        args = mock_process_chunks.call_args[0]
        assert args[0].name.endswith(f"chunked_{filename}.txt")

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
) -> None:
    """Test the document retrieval endpoint."""
    # First upload the document
    with open(test_pdf_document, "rb") as f:
        files = {"file": ("sample.pdf", f, "application/pdf")}
        upload_response = test_client.post("/api/documents/upload", files=files)

    assert upload_response.status_code == 200  # noqa: S101
    document_id = upload_response.json()["document_id"]

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
