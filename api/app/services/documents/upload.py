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
from typing import Any, Dict, Union

from fastapi import UploadFile

from app.core.config import Settings
from app.services.chunk import create_text_splitter
from app.services.datastore import DocumentMetadata, get_datastore_service
from app.services.embeddings import process_chunks
from app.services.process_docs import extract_docx_text, extract_pdf_text

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def process_uploaded_document(
    file: UploadFile, settings: Settings
) -> Dict[str, Any]:
    """Process an uploaded document through the RAG pipeline.

    Args:
        file: The uploaded file
        settings: Application settings

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

        # Extract text based on content type
        content_type = file.content_type
        if content_type == "application/pdf":
            extracted_text = extract_pdf_text(str(file_path))
        elif (
            content_type
            == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ):
            extracted_text = extract_docx_text(str(file_path))
        else:
            raise ValueError(
                f"Unsupported file content type: {content_type}. Could not determine how to extract text."
            )

        if not extracted_text.strip():
            raise ValueError("No text extracted from document")

        # Save document to datastore (permanently)
        await file.seek(0)  # Reset file position for saving
        document_metadata = await datastore.save_document(file, extracted_text)

        # Create text splitter
        text_splitter = create_text_splitter()

        # Split text into chunks
        chunks = text_splitter.split_text(extracted_text)

        # Save chunks to file in temporary directory
        chunks_file = temp_path / f"chunked_{file.filename}.txt"
        with open(chunks_file, "w", encoding="utf-8") as f:
            for i, chunk in enumerate(chunks):
                f.write(f"### CHUNK {i + 1}\n")
                f.write(chunk)
                f.write("\n\n")

        # Process chunks and store in ChromaDB with document metadata
        # Convert to dict if it's a Pydantic model
        metadata_dict = (
            document_metadata.model_dump()
            if hasattr(document_metadata, "model_dump")
            else dict(document_metadata)
        )
        process_chunks(chunks_file, settings.CHROMA_DIR, metadata_dict)

        # Return result dictionary with both attribute and dictionary access supported
        return {
            "document_id": document_metadata.document_id
            if hasattr(document_metadata, "document_id")
            else document_metadata["document_id"],
            "original_filename": document_metadata.original_filename
            if hasattr(document_metadata, "original_filename")
            else document_metadata["original_filename"],
            "num_chunks": len(chunks),
            "status": "success",
        }
