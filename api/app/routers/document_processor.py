"""Document processor routes.

This module provides FastAPI routes for document processing operations.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status, Form

from app.core.config import get_settings, Settings
from app.models.document_processor import ProcessedDocument
from app.services.document_processor import DocumentProcessor

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    responses={404: {"description": "Not found"}},
)


# Create a module-level singleton to avoid B008
settings_dependency = Depends(get_settings)


@router.post(
    "/process",
    response_model=ProcessedDocument,
    status_code=status.HTTP_201_CREATED,
    summary="Process a document",
    description="Upload and process a document through the RAG pipeline",
)
async def process_document(
    file: UploadFile,
    settings: Settings = settings_dependency,
) -> ProcessedDocument:
    """Process an uploaded document.

    Args:
        file: The file to process
        settings: Application settings

    Returns:
        ProcessedDocument with chunks and metadata

    Raises:
        HTTPException: If document processing fails
    """
    processor = DocumentProcessor()

    try:
        return await processor.process_file(file)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document processing failed: {str(e)}",
        ) from e
