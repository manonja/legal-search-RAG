"""Service for document operations.

This module provides functionality for retrieving and managing documents.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from app.core.struct_logger import log

from app.core.config import get_settings
from app.services.datastore import get_datastore_service, DocumentMetadata


async def get_document_content(document_id: str) -> Tuple[str, Dict[str, Any]]:
    """Get document content and metadata using the datastore service.

    Args:
        document_id: Document identifier (UUID)

    Returns:
        Tuple of (document content, metadata dictionary)

    Raises:
        FileNotFoundError: If document cannot be found
        IOError: If document cannot be read
    """
    # Remove any URL encoding
    log.info("Getting document content", document_id=document_id)

    # Get datastore service
    settings = get_settings()
    datastore = get_datastore_service(settings)

    # Try to get the document from datastore
    doc_metadata = datastore.get_document(document_id)

    if not doc_metadata:
        log.info("Document not found in datastore", document_id=document_id)
        raise FileNotFoundError(f"Document not found: {document_id}")

    # Get document text content from the extracted text
    text_content = datastore.get_text_content(document_id)

    if text_content:
        log.info("Retrieved text content", document_id=document_id)
        # Return document content and metadata from extracted text
        metadata = {
            "document_id": doc_metadata.document_id,
            "filename": doc_metadata.original_filename,
            "original_file_path": doc_metadata.original_file_path,
            "size": Path(doc_metadata.original_file_path).stat().st_size
            if Path(doc_metadata.original_file_path).exists()
            else 0,
            "source": f"datastore:{doc_metadata.document_id}",
        }
        return text_content, metadata
    else:
        log.info(
            "No extracted text found, trying to read original file",
            document_id=document_id,
        )
        raise FileNotFoundError(f"No extracted text found for document: {document_id}")
