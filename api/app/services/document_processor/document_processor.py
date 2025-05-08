"""Document processor service.

This module provides the main service for processing documents through the RAG pipeline:
1. Loading: Extract text and metadata from documents
2. Preprocessing: Clean and normalize text
3. Chunking: Split text into semantically coherent chunks
"""

import tempfile
from pathlib import Path
from typing import List, Dict, Any

from fastapi import UploadFile

from app.core.config import get_settings
from app.core.struct_logger import log
from app.models.document_processor import DocumentChunk, ProcessedDocument
from app.services.datastore import get_datastore_service
from app.services.document_processor.loaders import DocumentLoader
from app.services.document_processor.preprocessors import TextPreprocessor
from app.services.document_processor.chunkers import SemChunkChunker


class DocumentProcessor:
    """Service for processing documents through the RAG pipeline."""

    def __init__(self):
        """Initialize the document processor service."""
        self.settings = get_settings()
        self.datastore = get_datastore_service(self.settings)

        # Initialize preprocessor and chunker
        self.preprocessor = TextPreprocessor()
        self.chunker = SemChunkChunker()

    async def process_file(self, file: UploadFile) -> ProcessedDocument:
        """Process an uploaded file through the document processing pipeline.

        Args:
            file: The uploaded file

        Returns:
            ProcessedDocument with chunks and metadata

        Raises:
            ValueError: If file processing fails at any stage
        """
        # Basic validation
        if not file.filename:
            raise ValueError("Uploaded file must have a filename")

        # Get content type and confirm it's supported
        content_type = file.content_type
        if content_type == "application/octet-stream":
            # Fallback to file extension
            if file.filename.lower().endswith(".pdf"):
                content_type = "application/pdf"
            elif file.filename.lower().endswith(".docx"):
                content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            elif file.filename.lower().endswith(".doc"):
                content_type = "application/msword"

        # Process the file through the pipeline
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            file_path = temp_path / file.filename

            # Save uploaded file temporarily
            await file.seek(0)
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)

            # 1. LOADING: Extract text and metadata
            loader = DocumentLoader.get_loader_for_file(file_path, content_type)
            extracted_text, doc_metadata = loader.load(file_path)

            if not extracted_text.strip():
                raise ValueError("No text extracted from document")

            # 2. PREPROCESSING: Clean and normalize text
            processed_text = self.preprocessor.preprocess(extracted_text, doc_metadata)

            # Save document to datastore
            await file.seek(0)
            document_metadata = await self.datastore.save_document(file, processed_text)

            # Add document_id to metadata
            doc_metadata["document_id"] = document_metadata.document_id
            doc_metadata["original_filename"] = document_metadata.original_filename

            # 3. CHUNKING: Split text into semantic chunks
            chunk_data = self.chunker.chunk(processed_text, doc_metadata)

            # Create document chunks
            chunks = []
            for chunk in chunk_data:
                chunks.append(
                    DocumentChunk(
                        text=chunk["text"],
                        metadata=chunk["metadata"],
                        token_count=chunk["token_count"],
                        chunk_id=f"{document_metadata.document_id}_chunk_{chunk['metadata']['chunk_index']}",
                    )
                )

            # Return processed document
            return ProcessedDocument(
                document_id=document_metadata.document_id,
                original_filename=document_metadata.original_filename,
                chunks=chunks,
                metadata=doc_metadata,
                total_chunks=len(chunks),
            )
