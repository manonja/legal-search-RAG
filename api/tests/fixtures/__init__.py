"""Fixtures package for tests."""

from tests.fixtures.document_fixtures import (
    mock_extract_pdf_text,
    mock_extract_docx_text,
    mock_create_text_splitter,
    mock_process_chunks,
    mock_document_service,
    mock_document_not_found,
    mock_process_uploaded_document,
)

from tests.fixtures.router_fixtures import (
    test_dir,
    sample_document_content,
    sample_pdf_content,
    sample_docx_content,
    sample_txt_content,
    test_document_file,
    test_pdf_file,
    test_docx_file,
    test_txt_file,
    mock_get_document_content,
    mock_search_documents_router,
    mock_process_query_router,
    mock_process_uploaded_document_router,
)
