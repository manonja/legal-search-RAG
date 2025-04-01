"""Router for document upload operations.

This module provides endpoints for uploading and processing legal documents.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Dict, Any
import logging
from pathlib import Path

from app.services.documents.upload import process_uploaded_document
from app.core.config import get_settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        # Get settings
        settings = get_settings()

        # Process the uploaded document
        result = await process_uploaded_document(file, settings)

        return {
            "message": "Document processed successfully",
            "document_id": result["document_id"],
            "chunks": result["num_chunks"],
            "status": "success",
        }

    except Exception as e:
        logger.error(f"Error processing document: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to process document: {str(e)}"
        ) from e
