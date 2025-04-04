"""Router for document upload operations.

This module provides endpoints for uploading and processing legal documents.
"""

from pathlib import Path
from typing import Any, Dict, Union

from fastapi import APIRouter, File, HTTPException, UploadFile
from struct_logger import log

from app.core.config import get_settings
from app.services.datastore import DocumentMetadata
from app.services.documents.upload import process_uploaded_document

# Create router
router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload")
async def upload_document(file: UploadFile) -> Dict[str, Any]:
    """Upload and process a document.

    This endpoint:
    1. Saves the uploaded file
    2. Detects file type (PDF/DOCX)
    3. Converts to text
    4. Chunks the text
    5. Generates embeddings
    6. Stores in ChromaDB

    Args:
        file: The document file to upload

    Returns:
        Dict containing upload status and document ID

    Raises:
        HTTPException: If upload or processing fails
    """
    try:
        # Get content type from file
        content_type = file.content_type

        # If generic content type is detected, determine based on file extension
        if content_type == "application/octet-stream" and file.filename:
            if file.filename.lower().endswith(".pdf"):
                # Don't modify content_type directly, use an effective content type for validation
                effective_content_type = "application/pdf"
            elif file.filename.lower().endswith(".docx"):
                effective_content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            else:
                effective_content_type = content_type
        else:
            effective_content_type = content_type

        # Validate file content type
        allowed_mime_types = {
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }
        if effective_content_type not in allowed_mime_types:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {content_type}. Only PDF (application/pdf) and DOCX (application/vnd.openxmlformats-officedocument.wordprocessingml.document) files are supported.",
            )

        # Get settings
        settings = get_settings()

        # Process the uploaded document
        result = await process_uploaded_document(file, settings)

        # Extract values safely, supporting both dict and Pydantic model access patterns
        document_id = (
            result.get("document_id")
            if isinstance(result, dict)
            else getattr(result, "document_id", None)
        )
        original_filename = (
            result.get("original_filename")
            if isinstance(result, dict)
            else getattr(result, "original_filename", None)
        )
        num_chunks = (
            result.get("num_chunks")
            if isinstance(result, dict)
            else getattr(result, "num_chunks", 0)
        )

        if not document_id:
            raise HTTPException(
                status_code=500,
                detail="Document processing failed: No document ID returned",
            )

        return {
            "message": "Document processed successfully",
            "document_id": document_id,  # UUID-based ID
            "original_filename": original_filename,  # Return the original filename for reference
            "chunks": num_chunks,
            "status": "success",
        }

    except HTTPException:
        # Re-raise HTTP exceptions without modifying them
        raise
    except ValueError as e:
        log.error("Error processing document", error=str(e))
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        log.error("Error processing document", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to process document: {str(e)}"
        ) from e
