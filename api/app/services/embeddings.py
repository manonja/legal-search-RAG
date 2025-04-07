"""Handle document embeddings and vector store operations.

This module provides functionality to generate embeddings using OpenAI's API
and store them in a Chroma vector database for efficient retrieval.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from chromadb.utils.embedding_functions.openai_embedding_function import (
    OpenAIEmbeddingFunction,
)
from app.core.struct_logger import log
from tqdm import tqdm

from app.core.config import get_settings
from app.services.database.chroma import get_chroma_client

# Get application settings
settings = get_settings()

BATCH_SIZE = 100

# Initialize OpenAI embedding function
openai_ef = OpenAIEmbeddingFunction(
    api_key=settings.OPENAI_API_KEY,
    model_name=settings.EMBEDDING_MODEL,
)


def process_chunks(
    chunk_file: Path,
    chroma_dir: Path,
    document_metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Process all chunked documents and store their embeddings in Chroma.

    Args:
        chunk_file: Path to the chunked text file
        chroma_dir: Directory to store ChromaDB database
        document_metadata: Optional metadata for the document
    """

    # Use the shared Chroma client
    chroma_client = get_chroma_client()

    # Create or get collection with OpenAI embedding function
    collection = chroma_client.get_or_create_collection(
        name=settings.COLLECTION_NAME,
        metadata={"description": "Legal document embeddings"},
        embedding_function=openai_ef,  # type: ignore
    )

    doc_id = (
        document_metadata.get("document_id", chunk_file.stem)
        if document_metadata
        else chunk_file.stem
    )

    with open(chunk_file, "r", encoding="utf-8") as f:
        text = f.read()
        chunks = text.split("### CHUNK")[1:]  # Split on chunk markers
        chunks = [chunk.strip() for chunk in chunks]

    # Process chunks in batches
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]

        # Generate IDs for batch
        ids = [f"{doc_id}_chunk_{j + i + 1}" for j in range(len(batch))]

        # Prepare chunk metadata - ensuring required fields are present
        metadatas = []
        if document_metadata:
            # Ensure required keys are present in the provided metadata
            required_keys = ["document_id", "original_filename"]
            if not all(key in document_metadata for key in required_keys):
                log.error(
                    "Document metadata missing required keys for ChromaDB indexing",
                    missing_keys=[
                        k for k in required_keys if k not in document_metadata
                    ],
                    provided_metadata=document_metadata,
                )
                # Decide how to handle: raise error, skip, or add with partial data?
                # Raising an error is safest to ensure data integrity.
                raise ValueError(
                    "Document metadata missing required keys for indexing."
                )

            # Create metadata for each chunk in the batch
            for _ in batch:
                # Start with the essential fields for retrieval
                chunk_metadata = {
                    "document_id": document_metadata["document_id"],
                    "original_filename": document_metadata["original_filename"],
                    # Optionally include other fields if useful, e.g., original_file_path
                    # "original_file_path": document_metadata.get("original_file_path"),
                }
                # You could add other relevant per-chunk info here if needed (e.g., chunk number)
                metadatas.append(chunk_metadata)
        else:
            # Fallback if no document_metadata is provided (should ideally not happen in normal flow)
            # This maintains previous behavior but logs a warning.
            log.warning(
                "No document metadata provided for chunk indexing, using fallback.",
                chunk_file=str(chunk_file),
            )
            for _ in batch:
                metadatas.append({"source": str(chunk_file), "document_id": doc_id})

        # Add to Chroma (it will handle embeddings through OpenAI)
        collection.add(
            ids=ids,
            documents=batch,
            metadatas=metadatas,
        )
        log.info("Added batch of chunks", batch_size=len(batch))

    log.info(
        "Processing complete",
        document_id=doc_id,
        total_chunks=len(chunks),
        chroma_dir=str(chroma_dir),
    )
