"""Service for processing uploaded documents.

This module provides functionality to process uploaded documents through the RAG pipeline:
1. Save uploaded file
2. Convert to text
3. Chunk the text
4. Generate embeddings
5. Store in ChromaDB
"""

import logging
import os
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, Union

import semchunk
import tiktoken
from fastapi import UploadFile

from app.core.config import Settings
from app.services.datastore import DocumentMetadata, get_datastore_service
from app.services.embeddings import process_chunks
from app.services.process_docs import (
    extract_doc_text,
    extract_docx_text,
    extract_pdf_text,
)

# Configure logging
try:
    from app.core.struct_logger import log as logger
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)


async def process_uploaded_document(
    file: UploadFile, settings: Settings, collection_name: Optional[str] = None
) -> Dict[str, Any]:
    """Process an uploaded document through the RAG pipeline.

    Args:
        file: The uploaded file
        settings: Application settings
        collection_name: Optional name of collection to use

    Returns:
        Dict containing processing results

    Raises:
        ValueError: If file type is not supported
        Exception: If any processing step fails
    """
    # Get datastore service
    datastore = get_datastore_service(settings)

    # Create temporary directory for processing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Ensure filename exists
        if not file.filename:
            raise ValueError("Uploaded file must have a filename")

        # Construct the full path for the temporary file
        file_path = temp_path / file.filename

        # Save uploaded file temporarily for processing
        await file.seek(0)  # Reset file position
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        # Get content type and determine file type based on content type or extension if needed
        content_type = file.content_type
        if content_type == "application/octet-stream":
            # Fallback to file extension
            if file.filename.lower().endswith(".pdf"):
                content_type = "application/pdf"
            elif file.filename.lower().endswith(".docx"):
                content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            elif file.filename.lower().endswith(".doc"):
                content_type = "application/msword"

        # Extract text based on content type
        if content_type == "application/pdf":
            extracted_text = extract_pdf_text(str(file_path))
        elif (
            content_type
            == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ):
            extracted_text = extract_docx_text(str(file_path))
        elif content_type == "application/msword":
            extracted_text = extract_doc_text(str(file_path))
        else:
            raise ValueError(
                f"Unsupported file content type: {content_type}. Could not determine how to extract text."
            )

        if not extracted_text.strip():
            raise ValueError("No text extracted from document")

        # Save document to datastore (permanently)
        await file.seek(0)  # Reset file position for saving
        document_metadata = await datastore.save_document(file, extracted_text)

        # --- Start Semchunk Integration ---
        try:
            # Get the tokenizer encoding using the name from settings
            tokenizer = tiktoken.get_encoding(settings.SEMCHUNK_TOKENIZER)
            # Create the chunker function using chunkerify
            chunker = semchunk.chunkerify(
                tokenizer_or_token_counter=lambda text: len(tokenizer.encode(text)),
                chunk_size=settings.SEMCHUNK_CHUNK_SIZE,
            )
        except Exception as e:
            logger.error(
                "Failed to initialize semchunk chunker",
                tokenizer=settings.SEMCHUNK_TOKENIZER,
                error=str(e),
            )
            raise ValueError("Failed to initialize text chunker configuration.") from e

        # Perform chunking using semchunk
        try:
            chunks = chunker(extracted_text, overlap=settings.SEMCHUNK_OVERLAP_TOKENS)
            if not chunks:
                logger.warning(
                    "Semchunk produced no chunks for document",
                    document_id=document_metadata.document_id,
                    original_filename=document_metadata.original_filename,
                )
                raise ValueError("Text splitting resulted in zero chunks.")

        except Exception as e:
            logger.error(
                "Error during semchunk text splitting",
                document_id=document_metadata.document_id,
                error=str(e),
            )
            raise ValueError("Failed to split document text into chunks.") from e
        # --- End Semchunk Integration ---

        # Log the target collection
        target_collection = collection_name or settings.COLLECTION_NAME
        logger.info(
            "Processing document chunks",
            document_id=document_metadata.document_id,
            collection=target_collection,
            num_chunks=len(chunks),
        )

        # Process chunks and store embeddings
        process_chunks(
            chunks=chunks,
            chroma_dir=settings.CHROMA_DIR,
            document_metadata=document_metadata.model_dump(),
            collection_name=collection_name,
        )

        # Return processing results including document ID and chunk count
        return {
            "message": "Document processed successfully",
            "document_id": document_metadata.document_id,
            "original_filename": document_metadata.original_filename,
            "num_chunks": len(chunks),
            "collection": target_collection,
        }
