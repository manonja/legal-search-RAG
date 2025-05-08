"""Common fixtures for tests."""

from .document_fixtures import (
    mock_process_uploaded_document_router,
    mock_process_chunks,
    mock_extract_pdf_text,
    mock_extract_docx_text,
    mock_pdf_loader,
    mock_docx_loader,
)
from .file_fixtures import test_dir, test_pdf_file, test_docx_file, test_txt_file

__all__ = [
    "mock_process_uploaded_document_router",
    "mock_process_chunks",
    "mock_extract_pdf_text",
    "mock_extract_docx_text",
    "mock_pdf_loader",
    "mock_docx_loader",
    "test_dir",
    "test_pdf_file",
    "test_docx_file",
    "test_txt_file",
]
