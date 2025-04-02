"""Handle document embeddings and vector store operations.

This module provides functionality to generate embeddings using OpenAI's API
and store them in a Chroma vector database for efficient retrieval.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from tqdm import tqdm

from app.core.config import get_settings
from app.services.database.chroma import get_chroma_client

# Configure logging
logger = logging.getLogger(__name__)

# Get application settings
settings = get_settings()

BATCH_SIZE = 100

# Initialize OpenAI embedding function
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=settings.OPENAI_API_KEY,
    model_name=settings.EMBEDDING_MODEL,
)


def process_chunks(chunk_file: Path, chroma_dir: Path) -> None:
    """Process all chunked documents and store their embeddings in Chroma.

    Args:
        chunk_file: Path to the chunked text file
        chroma_dir: Directory to store ChromaDB database
    """

    # Use the shared Chroma client
    chroma_client = get_chroma_client()

    # Create or get collection with OpenAI embedding function
    collection = chroma_client.get_or_create_collection(
        name=settings.COLLECTION_NAME,
        metadata={"description": "Legal document embeddings"},
        embedding_function=openai_ef,
    )

    doc_id = chunk_file.stem

    with open(chunk_file, "r", encoding="utf-8") as f:
        text = f.read()
        chunks = text.split("### CHUNK")[1:]  # Split on chunk markers
        chunks = [chunk.strip() for chunk in chunks]

    # Process chunks in batches
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]

        # Generate IDs for batch
        ids = [f"{doc_id}_chunk_{j + i + 1}" for j in range(len(batch))]

        # Add to Chroma (it will handle embeddings through OpenAI)
        collection.add(
            ids=ids,
            documents=batch,
            metadatas=[{"source": str(chunk_file)} for _ in batch],
        )
        logger.info(f"Successfully added batch of {len(batch)} chunks")

    logger.info(f"Processing complete! Documents stored in Chroma at {chroma_dir}")
