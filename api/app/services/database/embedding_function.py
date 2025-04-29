"""
Custom embedding function using RunPod serverless for ChromaDB.
"""

import asyncio
from typing import List

from chromadb.api.types import Documents, EmbeddingFunction

from app.core.struct_logger import log

# Removing the circular import:
# from app.services.embeddings.factory import get_embedding_client


class HuggingFaceEmbeddingFunction(EmbeddingFunction):
    """Custom embedding function using RunPod for HuggingFace models."""

    def __init__(self, batch_size=32, client=None):
        """Initialize the embedding function with a RunPod client.

        Args:
            batch_size: Maximum number of texts to embed in a single API call.
            client: Optional embedding client. If None, a client will be created.
        """
        # Use the provided client or get a new one
        self.client = client or _get_embedding_client()
        self.batch_size = batch_size
        log.info(
            "HuggingFaceEmbeddingFunction initialized",
            model=self.client.model_name,
            batch_size=self.batch_size,
        )

    def __call__(self, texts: Documents) -> List[List[float]]:
        """Generate embeddings for the given texts using RunPod serverless.

        Args:
            texts: List of text documents to embed.

        Returns:
            List of embeddings as float vectors.
        """
        # Directly return empty list for empty input to avoid ChromaDB validation error
        if not texts or len(texts) == 0:
            log.debug("Empty input to embedding function, returning empty list")
            # Return empty list directly - ChromaDB will handle this special case
            return []

        # Process in event loop - convert async to sync
        try:
            # Get or create a new event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    raise RuntimeError("Event loop is closed")
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Run the async function in the event loop
            embeddings = loop.run_until_complete(self._process_embeddings(texts))
            return embeddings

        except Exception as e:
            log.error(
                "Error generating embeddings with HuggingFaceEmbeddingFunction",
                error=str(e),
                exc_info=True,
            )
            raise

    async def _process_embeddings(self, texts: Documents) -> List[List[float]]:
        """Process embeddings in batches using the RunPod client.

        Args:
            texts: List of text documents to embed.

        Returns:
            List of embeddings as float vectors.
        """
        all_embeddings = []

        # Process in batches to avoid overwhelming the API
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            log.debug(
                f"Processing embedding batch {i // self.batch_size + 1}, size {len(batch)}"
            )

            batch_embeddings = await self.client.create_embeddings(batch)
            all_embeddings.extend(batch_embeddings)

        return all_embeddings


def _get_embedding_client():
    """Lazy import the embedding client to avoid circular imports.

    Returns:
        An instance of the embedding client.
    """
    # Import here to avoid circular import with chroma.py
    from app.services.embeddings.factory import get_embedding_client

    return get_embedding_client()
