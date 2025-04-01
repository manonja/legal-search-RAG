"""Service for document operations.

This module provides functionality for retrieving and managing documents.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Tuple

from app.utils.env import get_docs_root, get_chunks_dir

logger = logging.getLogger(__name__)


async def find_document(document_id: str) -> Path:
    """Find a document by its ID in various directories.

    Args:
        document_id: Document identifier (filename)

    Returns:
        Path to the document file

    Raises:
        FileNotFoundError: If document cannot be found
    """
    # Remove any URL encoding
    document_id = document_id.replace("%20", " ")

    logger.info(f"Looking for document: {document_id}")

    # Look in processed docs directory first
    docs_root = get_docs_root()
    logger.info(f"Searching in processed docs directory: {docs_root}")

    # First try the exact path if it exists
    if (docs_root / document_id).exists():
        logger.info(f"Found document at exact path: {docs_root / document_id}")
        return docs_root / document_id

    # Then try finding it by name only, including in subdirectories
    for file in docs_root.rglob("*"):
        if file.name == document_id:
            logger.info(f"Found document by name: {file}")
            return file

    # If not found in processed docs, look in chunked docs directory
    chunks_dir = get_chunks_dir()
    logger.info(f"Searching in chunked docs directory: {chunks_dir}")

    # First try the exact path if it exists
    if (chunks_dir / document_id).exists():
        logger.info(f"Found document at exact path: {chunks_dir / document_id}")
        return chunks_dir / document_id

    # Then try finding it by name only, including in subdirectories
    for file in chunks_dir.rglob("*"):
        if file.name == document_id:
            logger.info(f"Found document by name: {file}")
            return file

    # If we get here, we didn't find the document
    logger.error(f"Document not found: {document_id}")
    raise FileNotFoundError(f"Document not found: {document_id}")


async def get_document_content(document_id: str) -> Tuple[str, Dict[str, Any]]:
    """Get document content and metadata from local storage.

    Args:
        document_id: Document identifier (filename)

    Returns:
        Tuple of (document content, metadata dictionary)

    Raises:
        FileNotFoundError: If document cannot be found
        IOError: If document cannot be read
    """
    try:
        # Try to locate the document file
        doc_file = await find_document(document_id)
        logger.info(f"Found document at: {doc_file}")

        # Read the file content
        with open(doc_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Get basic metadata
        metadata = {
            "filename": doc_file.name,
            "size": doc_file.stat().st_size,
            "last_modified": datetime.fromtimestamp(
                doc_file.stat().st_mtime
            ).isoformat(),
            "source": f"local:{doc_file}",
        }

        return content, metadata
    except Exception as e:
        logger.error(f"Error reading document {document_id}: {str(e)}")
        raise
