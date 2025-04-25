"""
Factory for creating the embedding client.
"""

from app.core.config import get_settings
from app.services.embeddings.runpod_embedding_client import RunPodEmbeddingClient
from app.core.struct_logger import log
from typing import Optional

# Simple cache for the client instance
_embedding_client_instance: Optional[RunPodEmbeddingClient] = None


def get_embedding_client() -> RunPodEmbeddingClient:
    """Get the configured embedding client (currently only RunPod).

    Raises:
        ConfigurationError: If RunPod embedding settings are missing.

    Returns:
        An instance of the RunPodEmbeddingClient.
    """
    global _embedding_client_instance
    if _embedding_client_instance is None:
        settings = get_settings()

        if not settings.RUNPOD_API_KEY or not settings.RUNPOD_EMBEDDING_ENDPOINT_ID:
            log.critical("RunPod API Key or Embedding Endpoint ID not configured.")
            raise ValueError(
                "RUNPOD_API_KEY and RUNPOD_EMBEDDING_ENDPOINT_ID must be set in environment variables."
            )

        log.info("Creating RunPod Embedding Client instance.")
        _embedding_client_instance = RunPodEmbeddingClient(
            api_key=settings.RUNPOD_API_KEY,
            endpoint_id=settings.RUNPOD_EMBEDDING_ENDPOINT_ID,
            model_name=settings.HF_EMBEDDING_MODEL,
        )

    return _embedding_client_instance
