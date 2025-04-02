"""Router for document operations.

This module provides endpoints for retrieving and managing documents.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from pathlib import Path

from app.services.documents.document import get_document_content
from app.models.document import DocumentResponse

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
