"""ChromaDB utility functions.

This module provides utility functions for interacting with ChromaDB.
"""

import logging
from typing import Optional

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from app.core.config import get_settings
from app.utils.env import get_chroma_dir

logger = logging.getLogger(__name__)

# Global collection instance
_collection: Optional[chromadb.Collection] = None


def initialize_chroma_client():
    """Initialize ChromaDB client based on environment configuration.

    Returns:
        chromadb.Client: Configured client for local storage
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


async def get_collection():
    """Get or create the ChromaDB collection.

    Returns:
        chromadb.Collection: The collection instance
    """
    global _collection

    if _collection is None:
        settings = get_settings()

        # Initialize client
        client = initialize_chroma_client()

        # Initialize OpenAI embedding function
        openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=settings.OPENAI_API_KEY,
            model_name=settings.EMBEDDING_MODEL,
        )

        try:
            _collection = client.get_collection(
                settings.COLLECTION_NAME, embedding_function=openai_ef
            )
            logger.info(
                f"Collection '{settings.COLLECTION_NAME}' exists with "
                f"{_collection.count()} embeddings"
            )
        except Exception:
            _collection = client.create_collection(
                name=settings.COLLECTION_NAME,
                embedding_function=openai_ef,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(f"Created new collection '{settings.COLLECTION_NAME}'")

    return _collection
