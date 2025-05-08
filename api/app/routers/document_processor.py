"""Document processor routes.

This module provides FastAPI routes for document processing operations.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status, Form
from sqlalchemy.orm import Session

from app.core.config import get_settings, Settings
from app.core.struct_logger import log
from app.models.document_processor import ProcessedDocument
from app.services.document_processor import DocumentProcessor
from app.services.embeddings import process_chunks
from app.services.database.vector_service import vector_service
from app.services.database.database import get_db

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    responses={404: {"description": "Not found"}},
)


# Create a module-level singleton to avoid B008
settings_dependency = Depends(get_settings)
db_dependency = Depends(get_db)


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
        # Process document only - this returns chunks but doesn't store embeddings
        processed_doc = await processor.process_file(file)
        return processed_doc
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


@router.post(
    "/process-and-save",
    response_model=ProcessedDocument,
    status_code=status.HTTP_201_CREATED,
    summary="Process a document and save to database",
    description="Upload, process, and store a document with vector embeddings in PostgreSQL",
)
async def process_and_save_document(
    file: UploadFile,
    db: Session = db_dependency,
    settings: Settings = settings_dependency,
) -> ProcessedDocument:
    """Process an uploaded document and save it to the database with embeddings.

    Args:
        file: The file to process
        db: Database session
        settings: Application settings

    Returns:
        ProcessedDocument with chunks and metadata

    Raises:
        HTTPException: If document processing fails
    """
    processor = DocumentProcessor()

    try:
        # Process document first
        processed_doc = await processor.process_file(file)

        # Store document and generate embeddings in one operation
        document_id = await vector_service.insert_document(db, processed_doc)

        log.info(
            "Document stored in database with embeddings",
            document_id=document_id,
            chunk_count=len(processed_doc.chunks),
        )

        return processed_doc
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


@router.post(
    "/process-and-embed",
    response_model=ProcessedDocument,
    status_code=status.HTTP_201_CREATED,
    summary="Process a document and store embeddings",
    description="Upload, process, and store embeddings for a document in the RAG pipeline",
)
async def process_and_embed_document(
    file: UploadFile,
    settings: Settings = settings_dependency,
) -> ProcessedDocument:
    """Process an uploaded document and store embeddings.

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
        # Process document first
        processed_doc = await processor.process_file(file)

        # Then handle embedding storage separately
        # Extract chunk texts
        chunk_texts = [chunk.text for chunk in processed_doc.chunks]

        # Create document metadata dict
        document_metadata = {
            "document_id": processed_doc.document_id,
            "original_filename": processed_doc.original_filename,
            # Include any other metadata from processed_doc.metadata you need
        }

        # Store embeddings
        process_chunks(
            chunks=chunk_texts,
            chroma_dir=settings.CHROMA_DIR,
            document_metadata=document_metadata,
        )

        log.info(
            "Stored embeddings for document chunks",
            document_id=processed_doc.document_id,
            chunk_count=len(processed_doc.chunks),
        )

        return processed_doc
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
