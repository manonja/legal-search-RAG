"""Service for processing uploaded documents.

This module provides functionality to process uploaded documents through the RAG pipeline:
1. Save uploaded file
2. Convert to text
3. Chunk the text
4. Generate embeddings
5. Store in ChromaDB
"""

import os
import tempfile
from pathlib import Path
from typing import Dict, Any
import logging
from fastapi import UploadFile

from app.services.process_docs import extract_pdf_text, extract_docx_text
from app.services.chunk import create_text_splitter
from app.services.embeddings import process_chunks
from app.core.config import Settings

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
    # Create temporary directory for processing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Save uploaded file
        file_path = temp_path / file.filename
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        # Detect file type and extract text
        if file.filename.lower().endswith(".pdf"):
            text = extract_pdf_text(str(file_path))
        elif file.filename.lower().endswith(".docx"):
            text = extract_docx_text(str(file_path))
        else:
            raise ValueError(f"Unsupported file type: {file.filename}")

        if not text.strip():
            raise ValueError("No text extracted from document")

        # Create text splitter
        text_splitter = create_text_splitter()

        # Split text into chunks
        chunks = text_splitter.split_text(text)

        # Save chunks to file
        chunks_file = temp_path / f"chunked_{file.filename}.txt"
        with open(chunks_file, "w", encoding="utf-8") as f:
            for i, chunk in enumerate(chunks):
                f.write(f"### CHUNK {i + 1}\n")
                f.write(chunk)
                f.write("\n\n")

        # Process chunks and store in ChromaDB
        process_chunks(chunks_file, settings.CHROMA_DIR)

        return {
            "document_id": file.filename,
            "num_chunks": len(chunks),
            "status": "success",
        }
