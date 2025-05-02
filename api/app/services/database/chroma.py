"""ChromaDB service for database initialization and management.

This module provides functionality for initializing and managing the ChromaDB connection.
"""

import time
from typing import Optional

import chromadb
from chromadb.config import Settings
from chromadb.errors import InvalidCollectionException
from app.core.struct_logger import log
from app.services.database.embedding_function import HuggingFaceEmbeddingFunction

from app.core.config import get_settings

# Global instances
_client: Optional[chromadb.ClientAPI] = None
_collection: Optional[chromadb.Collection] = None

MAX_CHROMA_CONNECTION_ATTEMPTS = 3


def get_chroma_client() -> chromadb.ClientAPI:
    """Get the shared ChromaDB client instance.

    Returns:
        chromadb.PersistentClient: The shared client instance
    """
    global _client
    if _client is None:
        _client = initialize_chroma_client()
    return _client


def initialize_chroma_client() -> chromadb.ClientAPI:
    """Initialize ChromaDB client based on environment configuration.

    Returns:
        chromadb.PersistentClient: Configured client for local storage
    """
    global _client

    # If client already exists, return it
    if _client is not None:
        return _client

    log.info("Initializing Chroma client")

    # Get ChromaDB directory
    settings = get_settings()
    chroma_dir = settings.CHROMA_DIR
    log.info("Using local ChromaDB storage", path=str(chroma_dir))

    # Create client with telemetry disabled
    _client = chromadb.PersistentClient(
        path=str(chroma_dir),
        settings=Settings(
            anonymized_telemetry=False,  # Disable telemetry
            allow_reset=True,
            is_persistent=True,
        ),
    )

    return _client


async def initialize_chroma_collection() -> chromadb.Collection:
    """Initialize ChromaDB collection with retry mechanism.

    Returns:
        chromadb.Collection: The initialized collection

    Raises:
        Exception: If initialization fails after all retries
    """
    global _collection, _client

    if _collection is not None:
        return _collection

    settings = get_settings()

    # Initialize HuggingFace embedding function through RunPod
    hf_ef = HuggingFaceEmbeddingFunction()

    # Initialize Chroma client and collection with a retry mechanism
    log.info("Initializing Chroma client and collection with HuggingFace embeddings")
    attempt = 0

    while attempt < MAX_CHROMA_CONNECTION_ATTEMPTS:
        try:
            attempt += 1
            log.info(
                "ChromaDB initialization attempt",
                attempt=attempt,
                max_attempts=MAX_CHROMA_CONNECTION_ATTEMPTS,
            )
            if _client is None:
                _client = initialize_chroma_client()
            # Test connection with a simple operation
            _client.list_collections()
            break
        except Exception as e:
            log.warning(
                "ChromaDB initialization attempt failed", attempt=attempt, error=str(e)
            )
            if attempt >= MAX_CHROMA_CONNECTION_ATTEMPTS:
                raise
            time.sleep(1)  # Wait before retrying

    # Check if collection exists before creating it
    try:
        if _client is None:
            raise ValueError("Chroma client not initialized")
        _collection = _client.get_collection(
            settings.COLLECTION_NAME, embedding_function=hf_ef
        )
        log.info(
            "Collection exists",
            name=settings.COLLECTION_NAME,
            embedding_count=_collection.count(),
        )
    except InvalidCollectionException as e:
        if _client is None:
            raise ValueError("Chroma client not initialized") from e
        # Only create collection if it doesn't exist
        log.info("Creating new collection", name=settings.COLLECTION_NAME)
        _collection = _client.create_collection(
            name=settings.COLLECTION_NAME,
            embedding_function=hf_ef,
            metadata={"hnsw:space": "cosine"},
        )

    log.info("Successfully initialized Chroma client and collection")
    return _collection


async def get_collection() -> chromadb.Collection | None:
    """Get the ChromaDB collection instance.

    Returns:
        chromadb.Collection: The collection instance
    """
    if _collection is None:
        await initialize_chroma_collection()
    return _collection
