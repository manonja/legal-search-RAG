"""Router for document upload operations.

This module provides endpoints for uploading and processing legal documents.

###############################################################################
# TODO: MIGRATE TO NEW API
#
# DEPRECATED: This router uses deprecated ChromaDB-based functionality.
# It should be migrated to use the new document_processor router and
# PostgreSQL/pgvector storage in a future update.
#
# - The /documents/upload endpoint should be migrated to use document_processor.py
#   and vector_service instead of the deprecated upload.py and embeddings.py
###############################################################################
"""

from pathlib import Path
from typing import Any, Dict, Union, List, Optional, Annotated

from fastapi import APIRouter, File, HTTPException, UploadFile, Depends, Form, Query
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.struct_logger import log
from app.services.datastore import DocumentMetadata
from app.services.document_processor import DocumentProcessor
from app.services.database.vector_service import vector_service
from app.services.database.database import get_db

# Create router
router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload")
async def upload_document(
    files: Annotated[List[UploadFile], File()], db: Annotated[Session, Depends(get_db)]
) -> Dict[str, Any]:
    """Upload and process one or more documents.

    This endpoint:
    1. Saves the uploaded file(s)
    2. Detects file type (PDF/DOCX/DOC)
    3. Converts to text
    4. Chunks the text
    5. Generates embeddings
    6. Stores in PostgreSQL with pgvector

    Args:
        files: List of document files to upload (supports single file or multiple files)
        db: Database session

    Returns:
        Dict containing upload status and document IDs

    Raises:
        HTTPException: If upload or processing fails
    """
    try:
        # Check if files were provided
        if not files:
            raise HTTPException(
                status_code=400,
                detail="No files were provided. Please upload at least one file.",
            )

        # Define allowed MIME types
        allowed_mime_types = {
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
        }

        # Get settings
        settings = get_settings()

        # Initialize processor
        processor = DocumentProcessor()

        # Process each file
        results = []
        failed = []

        for file in files:
            try:
                # Get content type
                content_type = file.content_type

                # If generic content type, determine based on file extension
                if content_type == "application/octet-stream" and file.filename:
                    if file.filename.lower().endswith(".pdf"):
                        effective_content_type = "application/pdf"
                    elif file.filename.lower().endswith(".docx"):
                        effective_content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    elif file.filename.lower().endswith(".doc"):
                        effective_content_type = "application/msword"
                    else:
                        effective_content_type = content_type
                else:
                    effective_content_type = content_type

                # Validate file content type
                if effective_content_type not in allowed_mime_types:
                    failed.append(
                        {
                            "filename": file.filename,
                            "error": f"Unsupported file type: {content_type}. Only PDF, DOCX, and DOC files are supported.",
                        }
                    )
                    continue

                # Process the uploaded document
                processed_doc = await processor.process_file(file)

                # Store document and generate embeddings in PostgreSQL using pgvector
                document_id = await vector_service.insert_document(db, processed_doc)

                # Log successful processing
                log.info(
                    "Document successfully processed and stored",
                    document_id=document_id,
                    original_filename=processed_doc.original_filename,
                    chunk_count=processed_doc.total_chunks,
                )

                # Add to results
                results.append(
                    {
                        "document_id": document_id,
                        "original_filename": processed_doc.original_filename,
                        "chunks": processed_doc.total_chunks,
                        "status": "success",
                    }
                )

            except Exception as e:
                # Log the error but continue processing other files
                log.error("Error processing file", filename=file.filename, error=str(e))
                failed.append({"filename": file.filename, "error": str(e)})

        # Prepare response
        response = {
            "message": f"Processed {len(results)} document(s) successfully"
            + (f", {len(failed)} failed" if failed else ""),
            "successful": results,
            "failed": failed,
            "total_processed": len(results),
            "total_failed": len(failed),
        }

        # If all files failed, return 400 status code
        if len(results) == 0 and len(failed) > 0:
            raise HTTPException(status_code=400, detail=response)

        return response

    except HTTPException:
        # Re-raise HTTP exceptions without modifying them
        raise
    except Exception as e:
        log.error("Error processing documents", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to process documents: {str(e)}"
        ) from e
