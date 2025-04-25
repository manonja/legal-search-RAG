"""
Factory for creating LLM clients based on configuration.

This module provides a factory function for creating the appropriate LLM client
based on the application configuration. It supports both OpenAI and RunPod vLLM.
"""

import openai
from app.core.config import get_settings
from app.core.struct_logger import log
from app.services.llm.runpod_client import RunPodClient

settings = get_settings()


def get_llm_client():
    """Factory function to get the appropriate LLM client.

    Returns:
        A client for interacting with LLMs, either OpenAI or RunPod.
    """
    # Check if RunPod is enabled and properly configured
    if (
        getattr(settings, "USE_RUNPOD", False)
        and getattr(settings, "RUNPOD_API_KEY", None)
        and getattr(settings, "RUNPOD_MIXTRAL_ENDPOINT_ID", None)
    ):
        log.info("Using RunPod vLLM client for LLM inference")
        return RunPodClient(
            api_key=settings.RUNPOD_API_KEY,
            endpoint_id=settings.RUNPOD_MIXTRAL_ENDPOINT_ID,
            model_name=getattr(
                settings, "RUNPOD_MODEL_NAME", "mistralai/Mixtral-8x7B-v0.1"
            ),
        )
    else:
        # Fallback to OpenAI
        log.info("Using OpenAI client for LLM inference")
        return openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
