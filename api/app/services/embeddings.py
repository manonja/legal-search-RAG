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
from struct_logger import log
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

        # Prepare chunk metadata
        metadatas = []
        for _ in batch:
            chunk_metadata = {"source": str(chunk_file)}
            if document_metadata:
                # Include document metadata with each chunk
                chunk_metadata.update(document_metadata)
            metadatas.append(chunk_metadata)

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
