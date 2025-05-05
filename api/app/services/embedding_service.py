from typing import List, Dict, Any
import requests

from app.core.config import get_settings
from app.core.struct_logger import log
from app.services.embeddings.factory import get_embedding_client

settings = get_settings()


class EmbeddingService:
    """Service for generating text embeddings using RunPod."""

    def __init__(self):
        """Initialize the embedding service."""
        log.info("Embedding Service initialization: Creating client")
        self.client = get_embedding_client()

        # Optional health check like in LlmChatService
        self._check_health()
        log.info("Embedding Service initialized")

    def _check_health(self):
        """Check the health of the RunPod embedding endpoint."""
        try:
            response = requests.get(
                f"https://api.runpod.ai/v2/{settings.RUNPOD_EMBEDDING_ENDPOINT_ID}/health",
                headers={
                    "Authorization": f"Bearer {settings.RUNPOD_API_KEY}",
                    "Content-Type": "application/json",
                },
                timeout=30,
            )
            if response.status_code == 200:
                log.info(
                    "Embedding service health check successful",
                    response=response.json(),
                )
            else:
                log.warning(
                    "Embedding service health check failed",
                    status_code=response.status_code,
                    response_text=response.text,
                )
        except Exception as e:
            log.error("Error checking embedding service health", error=str(e))

    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for the provided texts.

        Args:
            texts: List of texts to generate embeddings for.

        Returns:
            List of embedding vectors as floats.
        """
        if not texts:
            return []

        log.info(f"Generating embeddings for {len(texts)} texts")

        # In EmbeddingService.generate_embeddings
        try:
            embeddings = await self.client.create_embeddings(texts)

            # Additional validation that response format matches expectations
            if not embeddings or not isinstance(embeddings[0], list):
                log.error("Unexpected embedding format returned from API")
                dimension = 768
                return [[0.0] * dimension for _ in range(len(texts))]

            log.info(f"Successfully generated {len(embeddings)} embeddings")
            return embeddings
        except Exception as e:
            log.error("Error generating embeddings", error=str(e))
            # Return empty embeddings in case of error
            # Could also raise an HTTPException here
            dimension = 768  # Default for legal-bert
            return [[0.0] * dimension for _ in range(len(texts))]
