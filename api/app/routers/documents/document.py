"""Router for document operations.

This module provides endpoints for retrieving and managing documents.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from typing import Dict, Any
from pathlib import Path

from app.services.documents.document import get_document_content
from app.models.document import DocumentResponse
from app.core.config import get_settings
from app.services.datastore import get_datastore_service
from app.core.struct_logger import log

# Create router
router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(document_id: str) -> DocumentResponse:
    """Retrieve a full document by its ID.

    Args:
        document_id: Document identifier (filename)

    Returns:
        DocumentResponse containing the full document and metadata

    Raises:
        HTTPException: If document is not found or can't be accessed
    """
    try:
        # Get the document content and metadata
        try:
            content, metadata = await get_document_content(document_id)
        except FileNotFoundError as e:
            raise HTTPException(status_code=404, detail="Document not found") from e
        except IOError as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to read document: {str(e)}"
            ) from e

        # Return document response
        return DocumentResponse(
            content=content,
            metadata=metadata,
            source=metadata.get("source", ""),
            chunks=[],  # Empty chunks since we're retrieving whole document
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve document: {str(e)}"
        ) from e


@router.get("/{document_id}/download")
async def download_document(document_id: str):
    """Download the original document file by its ID.

    Args:
        document_id: Document identifier (UUID)

    Returns:
        FileResponse streaming the original document content.

    Raises:
        HTTPException: If document or original file is not found.
    """
    try:
        log.info("Request received to download document", document_id=document_id)
        settings = get_settings()
        datastore = get_datastore_service(settings)

        # Retrieve metadata first to get the original filename
        metadata = datastore.get_document(document_id)
        if not metadata:
            log.warning(
                "Document metadata not found for download", document_id=document_id
            )
            raise HTTPException(status_code=404, detail="Document not found")

        # Get the path to the original file
        original_file_path = datastore.get_original_file_path(document_id)

        if not original_file_path or not original_file_path.exists():
            log.warning(
                "Original file not found for download",
                document_id=document_id,
                path_checked=str(original_file_path),
            )
            raise HTTPException(status_code=404, detail="Original file not found")

        log.info(
            "Found original file, preparing download",
            document_id=document_id,
            file_path=str(original_file_path),
            original_filename=metadata.original_filename,
        )

        # Return the file using FileResponse
        return FileResponse(
            path=original_file_path,
            filename=metadata.original_filename,
            media_type="application/octet-stream",
        )

    except HTTPException:
        raise
    except Exception as e:
        log.error(
            "Error during document download", document_id=document_id, error=str(e)
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to download document: {str(e)}"
        ) from e
