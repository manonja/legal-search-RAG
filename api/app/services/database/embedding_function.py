"""
Custom embedding function using RunPod serverless for ChromaDB.
"""

import asyncio
from typing import List, Any

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
        self.embedding_dim = 768  # Default for legal-bert
        log.info(
            "HuggingFaceEmbeddingFunction initialized",
            model=self.client.model_name,
            batch_size=self.batch_size,
        )

        # Create a cache for embeddings
        self._embeddings_cache = {}

    def __call__(self, texts: Documents) -> List[List[float]]:
        """Generate embeddings for the provided texts.

        This is the main entry point called by ChromaDB, which expects a synchronous function.
        We need to handle the async nature of the RunPod client properly.

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
                [0.0] * self.embedding_dim
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
                batch_embeddings = await self.client.create_embeddings(batch)

                # Validate the batch embeddings
                if not isinstance(batch_embeddings, list):
                    log.error(
                        f"Unexpected batch embeddings type: {type(batch_embeddings)}",
                        batch_idx=i // self.batch_size + 1,
                    )
                    # Return placeholder embeddings of the correct dimension
                    return [[0.0] * self.embedding_dim for _ in range(len(texts))]

                # If this is an asyncio.Task, that's a problem
                if isinstance(batch_embeddings, asyncio.Task):
                    log.error(
                        "create_embeddings returned an asyncio.Task instead of embeddings",
                        batch_idx=i // self.batch_size + 1,
                    )
                    # Return placeholder embeddings of the correct dimension
                    return [[0.0] * self.embedding_dim for _ in range(len(texts))]

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
                return [[0.0] * self.embedding_dim for _ in range(len(texts))]

        return all_embeddings


def _get_embedding_client():
    """Get the embedding client singleton.

    This function avoids circular imports.

    Returns:
        The embedding client instance.
    """
    from app.services.embeddings.factory import get_embedding_client

    return get_embedding_client()
