"""Type stubs for google.generativeai.

This module provides type information for the google.generativeai package,
focusing on the core functionality used in our RAG system.
"""

from typing import Any, Dict, Optional, Union

class GenerateContentResponse:
    """Response from generate_content with text content."""

    text: str
    prompt_feedback: Optional[Dict[str, Any]]

class GenerativeModel:
    """Generative model class for text generation.

    Attributes:
        model_name: The name of the model being used
    """

    model_name: str

    def __init__(self, model_name: str) -> None: ...
    def generate_content(
        self,
        prompt: Union[str, Dict[str, Any]],
        *,
        safety_settings: Optional[Dict[str, Any]] = None,
        generation_config: Optional[Dict[str, Any]] = None,
    ) -> GenerateContentResponse:
        """Generate content from a prompt.

        Args:
            prompt: The input prompt as string or structured content
            safety_settings: Optional safety configuration
            generation_config: Optional generation parameters

        Returns:
            Response containing generated text and feedback
        """
        ...

def configure(
    api_key: str,
    *,
    client_options: Optional[Dict[str, Any]] = None,
    transport: Optional[str] = None,
) -> None:
    """Configure the Generative AI client.

    Args:
        api_key: The API key for authentication
        client_options: Optional client configuration
        transport: Optional transport configuration
    """
    ...
