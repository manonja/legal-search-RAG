"""Router for document operations.

This module provides endpoints for retrieving and managing documents.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Body
from fastapi.responses import FileResponse, JSONResponse
from typing import Dict, Any, List
from pathlib import Path

from app.services.documents.document import get_document_content
from app.models.document import DocumentResponse
from app.core.config import get_settings
from app.services.datastore import get_datastore_service, DatastoreService
from app.core.struct_logger import log

# Create router
router = APIRouter(prefix="/documents", tags=["documents"])


# Define dependency function
def get_datastore():
    """Dependency for DatastoreService."""
    settings = get_settings()
    return get_datastore_service(settings)


# Define module-level dependency
datastore_dependency = Depends(get_datastore)


@router.get("", response_model=List[str])
async def list_documents(
    datastore: DatastoreService = datastore_dependency,
):
    """List all available document IDs."""
    try:
        document_ids = datastore.list_document_ids()
        return document_ids
    except Exception as e:
        log.error("Failed to list documents", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list documents",
        ) from e


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: str, datastore: DatastoreService = datastore_dependency
) -> DocumentResponse:
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


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    datastore: DatastoreService = datastore_dependency,
):
    """Delete a document by its ID."""
    try:
        deleted = datastore.delete_document(document_id)
        if not deleted:
            log.warning(
                "Attempted to delete non-existent document", document_id=document_id
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found or could not be deleted",
            )
        log.info("Document deleted via API", document_id=document_id)
        # Simply return None, FastAPI will handle the 204 status code
        return None
    except HTTPException:
        raise  # Re-raise HTTPException from the datastore or not found check
    except Exception as e:
        log.error(
            "Error deleting document via API",
            document_id=document_id,
            error=str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document",
        ) from e


@router.get("/{document_id}/download")
async def download_document(
    document_id: str, datastore: DatastoreService = datastore_dependency
):
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
