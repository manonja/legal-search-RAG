"""
Factory for creating LLM clients based on configuration.

This module provides a factory function for creating the appropriate LLM client
based on the application configuration. It exclusively uses RunPod vLLM for
a privacy-focused architecture.
"""

from app.core.config import get_settings
from app.core.struct_logger import log
from app.services.llm.runpod_client import RunPodClient

settings = get_settings()


def get_llm_client():
    """Factory function to get the RunPod LLM client.

    Returns:
        A client for interacting with LLMs via RunPod.

    Raises:
        ValueError: If RunPod is not properly configured.
    """
    # Check if RunPod is properly configured
    if not settings.RUNPOD_API_KEY or not settings.RUNPOD_MIXTRAL_ENDPOINT_ID:
        log.error(
            "RunPod configuration missing. Required for privacy-focused deployment."
        )
        raise ValueError(
            "RUNPOD_API_KEY and RUNPOD_MIXTRAL_ENDPOINT_ID must be set for privacy-focused deployment."
        )

    log.info("Using RunPod vLLM client for LLM inference")
    return RunPodClient(
        api_key=settings.RUNPOD_API_KEY,
        endpoint_id=settings.RUNPOD_MIXTRAL_ENDPOINT_ID,
        model_name=getattr(
            settings, "RUNPOD_MODEL_NAME", "mistralai/Mixtral-8x7B-v0.1"
        ),
    )
