#!/usr/bin/env python
"""
Create a new ChromaDB collection with HuggingFace embeddings.

This script creates a fresh ChromaDB collection with the legal-bert-base-uncased model from HuggingFace.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import app modules
script_dir = Path(__file__).parent.absolute()
project_root = script_dir.parent
sys.path.append(str(project_root))

from app.core.config import get_settings
from app.services.database.embedding_function import HuggingFaceEmbeddingFunction
from app.core.struct_logger import log
import chromadb
from chromadb.config import Settings


async def create_new_hf_collection(collection_name=None, force_recreate=False):
    """Create a new ChromaDB collection with HuggingFace embeddings.

    Args:
        collection_name: Optional custom collection name. If None, uses {COLLECTION_NAME}_hf
        force_recreate: If True, delete the collection if it already exists

    Returns:
        The created ChromaDB collection
    """
    settings = get_settings()

    # Use custom name or default to {collection_name}_hf
    if collection_name is None:
        collection_name = f"{settings.COLLECTION_NAME}_hf"

    log.info(f"Creating HuggingFace collection: {collection_name}")

    # Initialize the HuggingFace embedding function
    hf_ef = HuggingFaceEmbeddingFunction()

    # Create ChromaDB client
    chroma_dir = settings.CHROMA_DIR
    log.info(f"Using ChromaDB directory: {chroma_dir}")

    client = chromadb.PersistentClient(
        path=str(chroma_dir),
        settings=Settings(
            anonymized_telemetry=False,
            allow_reset=True,
            is_persistent=True,
        ),
    )

    # Check if collection exists
    existing_collections = client.list_collections()
    collection_exists = any(c.name == collection_name for c in existing_collections)

    if collection_exists:
        if force_recreate:
            log.warning(f"Deleting existing collection: {collection_name}")
            client.delete_collection(collection_name)
        else:
            log.info(
                f"Collection {collection_name} already exists. Use --force to recreate."
            )
            return client.get_collection(collection_name, embedding_function=hf_ef)

    # Create the collection with HuggingFace embeddings
    log.info(f"Creating new collection: {collection_name}")
    collection = client.create_collection(
        name=collection_name,
        embedding_function=hf_ef,
        metadata={
            "hnsw:space": "cosine",
            "embedding_model": settings.HF_EMBEDDING_MODEL,
        },
    )

    log.info(f"Successfully created collection: {collection_name}")
    return collection


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Create a new ChromaDB collection with HuggingFace embeddings"
    )
    parser.add_argument(
        "--name", help="Custom collection name (default: {COLLECTION_NAME}_hf)"
    )
    parser.add_argument(
        "--force", action="store_true", help="Force recreation if collection exists"
    )
    args = parser.parse_args()

    asyncio.run(create_new_hf_collection(args.name, args.force))
    log.info("Collection creation completed")
