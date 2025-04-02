"""ChromaDB service for database initialization and management.

This module provides functionality for initializing and managing the ChromaDB connection.
"""

import logging
import time
from typing import Optional

import chromadb
from chromadb.config import Settings
from chromadb.errors import InvalidCollectionException
from chromadb.utils import embedding_functions

from app.core.config import get_settings
from app.utils import get_chroma_dir

logger = logging.getLogger(__name__)

# Global collection instance
_collection: Optional[chromadb.Collection] = None


def initialize_chroma_client() -> chromadb.PersistentClient:
    """Initialize ChromaDB client based on environment configuration.

    Returns:
        chromadb.PersistentClient: Configured client for local storage
    """
    logger.info("Initializing Chroma client")

    # Get ChromaDB directory
    chroma_dir = get_chroma_dir()
    logger.info(f"Using local ChromaDB storage: {chroma_dir}")

    # Create client with telemetry disabled
    return chromadb.PersistentClient(
        path=str(chroma_dir),
        settings=Settings(
            anonymized_telemetry=False,  # Disable telemetry
            allow_reset=True,
            is_persistent=True,
        ),
    )


async def initialize_chroma_collection() -> chromadb.Collection:
    """Initialize ChromaDB collection with retry mechanism.

    Returns:
        chromadb.Collection: The initialized collection

    Raises:
        Exception: If initialization fails after all retries
    """
    global _collection

    if _collection is not None:
        return _collection

    settings = get_settings()

    # Initialize OpenAI embedding function
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=settings.OPENAI_API_KEY,
        model_name=settings.EMBEDDING_MODEL,
    )

    # Initialize Chroma client and collection with a retry mechanism
    logger.info("Initializing Chroma client and collection")
    max_attempts = 3
    attempt = 0
    client = None

    while attempt < max_attempts:
        try:
            attempt += 1
            logger.info(f"ChromaDB initialization attempt {attempt}/{max_attempts}")
            client = initialize_chroma_client()
            # Test connection with a simple operation
            client.list_collections()
            break
        except Exception as e:
            logger.warning(f"ChromaDB initialization attempt {attempt} failed: {e}")
            if attempt >= max_attempts:
                raise
            time.sleep(1)  # Wait before retrying

    # Check if collection exists before creating it
    try:
        _collection = client.get_collection(
            settings.COLLECTION_NAME, embedding_function=openai_ef
        )
        logger.info(
            f"Collection '{settings.COLLECTION_NAME}' exists with "
            f"{_collection.count()} embeddings"
        )
    except (ValueError, InvalidCollectionException):
        # Only create collection if it doesn't exist
        logger.info(f"Creating new collection '{settings.COLLECTION_NAME}'")
        _collection = client.create_collection(
            name=settings.COLLECTION_NAME,
            embedding_function=openai_ef,
            metadata={"hnsw:space": "cosine"},
        )

    logger.info("Successfully initialized Chroma client and collection")
    return _collection


async def get_collection() -> chromadb.Collection:
    """Get the ChromaDB collection instance.

    Returns:
        chromadb.Collection: The collection instance
    """
    if _collection is None:
        await initialize_chroma_collection()
    return _collection
