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
_runpod_collection: Optional[chromadb.Collection] = None

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


async def initialize_chroma_collection(
    custom_collection_name: Optional[str] = None,
) -> chromadb.Collection:
    """Initialize ChromaDB collection with retry mechanism.

    Args:
        custom_collection_name: Optional custom collection name to use

    Returns:
        chromadb.Collection: The initialized collection

    Raises:
        Exception: If initialization fails after all retries
    """
    global _collection, _client

    # If we're requesting a specific collection name, don't use cached collection
    if custom_collection_name is None and _collection is not None:
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

    # If a custom collection name is provided, use that directly
    if custom_collection_name is not None:
        try:
            if _client is None:
                raise ValueError("Chroma client not initialized")

            try:
                # Try to get the custom collection
                custom_collection = _client.get_collection(
                    custom_collection_name, embedding_function=hf_ef
                )
                log.info(
                    "Using custom collection",
                    name=custom_collection_name,
                    embedding_count=custom_collection.count(),
                )
                # Don't cache this in _collection as it's a one-time use
                return custom_collection
            except InvalidCollectionException:
                log.warning(
                    f"Custom collection '{custom_collection_name}' doesn't exist",
                )
                # Fall through to standard collection logic
        except Exception as e:
            log.warning(
                f"Failed to use custom collection '{custom_collection_name}'",
                error=str(e),
            )
            # Fall through to standard collection logic

    # First try to get the RunPod collection
    try:
        if _client is None:
            raise ValueError("Chroma client not initialized")

        # Define RunPod collection name
        runpod_collection_name = f"{settings.COLLECTION_NAME}_runpod"

        try:
            # Try to get the RunPod collection first
            _collection = _client.get_collection(
                runpod_collection_name, embedding_function=hf_ef
            )
            log.info(
                "Using RunPod collection",
                name=runpod_collection_name,
                embedding_count=_collection.count(),
            )
        except InvalidCollectionException:
            log.info(
                "RunPod collection doesn't exist, creating new collection",
                name=runpod_collection_name,
            )
            # Create the RunPod collection if it doesn't exist
            _collection = _client.create_collection(
                name=runpod_collection_name,
                embedding_function=hf_ef,
                metadata={"hnsw:space": "cosine"},
            )
    except Exception as e:
        # If there's an issue with the RunPod collection, fall back to the standard collection
        log.warning(
            "Failed to use RunPod collection, falling back to standard collection",
            error=str(e),
        )
        try:
            if _client is None:
                raise ValueError("Chroma client not initialized")
            # Try to get the standard collection
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
            # Create the standard collection if it doesn't exist
            log.info("Creating new collection", name=settings.COLLECTION_NAME)
            _collection = _client.create_collection(
                name=settings.COLLECTION_NAME,
                embedding_function=hf_ef,
                metadata={"hnsw:space": "cosine"},
            )

    log.info("Successfully initialized Chroma client and collection")
    return _collection


async def get_collection(
    custom_collection_name: Optional[str] = None,
) -> chromadb.Collection | None:
    """Get the ChromaDB collection instance.

    Args:
        custom_collection_name: Optional custom collection name to use instead of default

    Returns:
        chromadb.Collection: The collection instance
    """
    if custom_collection_name is not None:
        # If asking for a custom collection, don't cache it
        return await initialize_chroma_collection(custom_collection_name)

    # Otherwise use/initialize the default collection
    global _collection
    if _collection is None:
        await initialize_chroma_collection()
    return _collection
