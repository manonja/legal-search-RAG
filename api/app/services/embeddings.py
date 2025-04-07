"""Handle document embeddings and vector store operations.

This module provides functionality to generate embeddings using OpenAI's API
and store them in a Chroma vector database for efficient retrieval.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional, List

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
    chunks: List[str],
    chroma_dir: Path,
    document_metadata: Dict[str, Any],
) -> None:
    """Process document chunks and store their embeddings in Chroma.

    Args:
        chunks: List of text chunks for the document
        chroma_dir: Directory containing ChromaDB database (may become redundant)
        document_metadata: Required metadata dictionary for the document,
                           must contain 'document_id' and 'original_filename'.
    """

    # Use the shared Chroma client
    chroma_client = get_chroma_client()

    # Create or get collection with OpenAI embedding function
    collection = chroma_client.get_or_create_collection(
        name=settings.COLLECTION_NAME,
        metadata={"description": "Legal document embeddings"},
        embedding_function=openai_ef,  # type: ignore
    )

    # Get doc_id reliably from the required document_metadata
    if (
        "document_id" not in document_metadata
        or "original_filename" not in document_metadata
    ):
        log.error(
            "process_chunks called without required keys in document_metadata",
            required_keys=["document_id", "original_filename"],
            provided_metadata=document_metadata,
        )
        raise ValueError(
            "process_chunks requires document_metadata with document_id and original_filename."
        )
    doc_id = document_metadata["document_id"]
    original_filename = document_metadata["original_filename"]

    # Check if there are any chunks to process
    if not chunks:
        log.warning(
            "process_chunks called with an empty list of chunks", document_id=doc_id
        )
        return  # Nothing to add to the database

    # Process chunks in batches
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]

        # Generate IDs for batch
        ids = [f"{doc_id}_chunk_{j + i + 1}" for j in range(len(batch))]

        # Prepare chunk metadata - explicitly use required fields
        metadatas = []
        # Create metadata for each chunk in the batch
        for _ in batch:
            # Start with the essential fields for retrieval
            chunk_metadata = {
                "document_id": doc_id,
                "original_filename": original_filename,
                # Optionally include other fields if useful, e.g., original_file_path
                # "original_file_path": document_metadata.get("original_file_path"),
            }
            metadatas.append(chunk_metadata)

        # Add to Chroma (it will handle embeddings through OpenAI)
        try:
            collection.add(
                ids=ids,
                documents=batch,
                metadatas=metadatas,
            )
            log.info(
                "Added batch of chunks to ChromaDB",
                batch_size=len(batch),
                document_id=doc_id,
            )
        except Exception as e:
            log.error(
                "Failed to add chunk batch to ChromaDB",
                document_id=doc_id,
                batch_start_index=i,
                error=str(e),
            )
            # Depending on requirements, might want to raise or continue to next batch
            raise  # Re-raise exception to signal failure in upload process

    log.info(
        "Chunk processing complete for document",
        document_id=doc_id,
        total_chunks=len(chunks),
        chroma_collection=settings.COLLECTION_NAME,
    )
