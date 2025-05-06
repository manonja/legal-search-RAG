"""
Custom embedding function for ChromaDB using the app's EmbeddingService.

This provides a ChromaDB-compatible embedding function that leverages
the application's embedding service with advanced features like
caching, batching, and robust error handling.
"""

import asyncio
from typing import List, Optional, Dict, Any, Union

from chromadb.api.types import Documents, EmbeddingFunction

from app.core.struct_logger import log
from app.services.embedding_service import EmbeddingService


class AppEmbeddingFunction(EmbeddingFunction):
    """ChromaDB-compatible embedding function using the application's EmbeddingService.

    Features:
    - Embedding result caching to avoid redundant API calls
    - Batch processing for efficient handling of large document sets
    - Comprehensive error handling and fallback mechanisms
    - Bridging between ChromaDB's synchronous API and our async EmbeddingService
    """

    def __init__(self, batch_size: int = 32):
        """Initialize the embedding function with application's EmbeddingService.

        Args:
            batch_size: Maximum number of texts to embed in a single API call.
        """
        # Create the embedding service
        self.embedding_service = EmbeddingService()
        self.batch_size = batch_size
        self._dimensionality: Optional[int] = None
        self._embeddings_cache: Dict[int, List[List[float]]] = {}

        log.info(
            "AppEmbeddingFunction initialized",
            batch_size=self.batch_size,
        )

    def __call__(self, texts: Documents) -> List[List[float]]:
        """Generate embeddings for the provided texts.

        This is the main entry point called by ChromaDB, which expects a synchronous function.
        We handle the async nature of the EmbeddingService by running it in a new event loop.

        Args:
            texts: List of text documents to embed.

        Returns:
            List of embeddings as float vectors.
        """
        if not texts:
            return []

        # Use a cache key based on the content of texts
        cache_key = hash(tuple(texts))

        # Return cached result if available
        if cache_key in self._embeddings_cache:
            log.debug(f"Returning cached embeddings for {len(texts)} texts")
            return self._embeddings_cache[cache_key]

        log.info(f"Generating embeddings for {len(texts)} texts")

        # Get a new event loop and run until complete
        result = self._run_in_new_loop(self._process_embeddings, texts)

        # Cache the results for future use
        self._embeddings_cache[cache_key] = result
        return result

    def _run_in_new_loop(self, coro_func, *args, **kwargs):
        """Run a coroutine in a new event loop, ensuring it completes.

        Args:
            coro_func: Coroutine function to run
            *args: Arguments to pass to the coroutine
            **kwargs: Keyword arguments to pass to the coroutine

        Returns:
            The result of the coroutine
        """
        # Create a new loop for this specific embedding operation
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            return loop.run_until_complete(coro_func(*args, **kwargs))
        except Exception as e:
            log.error(
                "Error in embedding function event loop", error=str(e), exc_info=True
            )
            # In case of error, return placeholder embeddings
            return [
                [0.0] * self.dimensionality
                for _ in range(
                    len(args[0]) if args and isinstance(args[0], list) else 1
                )
            ]
        finally:
            loop.close()

    async def _process_embeddings(self, texts: Documents) -> List[List[float]]:
        """Process embeddings asynchronously in batches.

        Args:
            texts: List of text documents to embed.

        Returns:
            List of embeddings as float vectors.
        """
        if not texts:
            return []

        all_embeddings = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i : i + self.batch_size]
            try:
                log.debug(f"Processing batch {i // self.batch_size + 1}")
                batch_embeddings = await self.embedding_service.generate_embeddings(
                    batch
                )

                # Validate the batch embeddings
                if not isinstance(batch_embeddings, list):
                    log.error(
                        f"Unexpected batch embeddings type: {type(batch_embeddings)}",
                        batch_idx=i // self.batch_size + 1,
                    )
                    # Return placeholder embeddings of the correct dimension
                    return [[0.0] * self.dimensionality for _ in range(len(texts))]

                # Save dimensionality for future reference
                if (
                    batch_embeddings
                    and len(batch_embeddings) > 0
                    and self._dimensionality is None
                ):
                    self._dimensionality = len(batch_embeddings[0])

                all_embeddings.extend(batch_embeddings)
            except Exception as e:
                log.error(
                    f"Error embedding batch {i // self.batch_size + 1}",
                    error=str(e),
                    start_idx=i,
                    end_idx=min(i + self.batch_size, len(texts)),
                    exc_info=True,
                )
                # If we fail, return placeholder embeddings
                return [[0.0] * self.dimensionality for _ in range(len(texts))]

        return all_embeddings

    @property
    def dimensionality(self) -> int:
        """Get the dimensionality of the embedding vectors.

        Returns:
            int: The dimensionality of the embedding vectors
        """
        if self._dimensionality is None:
            # Default dimensionality (e.g., for OpenAI embeddings or legal-bert)
            return 768
        return self._dimensionality
