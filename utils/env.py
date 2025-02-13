"""Environment variable configuration module.

This module handles loading and validation of environment variables
required by the application.
"""

import os
from typing import Optional

from dotenv import load_dotenv


def load_env_variables() -> None:
    """Load environment variables from .env file."""
    load_dotenv()


def get_google_api_key() -> str:
    """Get the Google API key from environment variables.

    Returns:
        str: The Google API key.

    Raises:
        ValueError: If the API key is not set.
    """
    api_key: Optional[str] = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY environment variable is not set. "
            "Please set it in your .env file."
        )
    return api_key
