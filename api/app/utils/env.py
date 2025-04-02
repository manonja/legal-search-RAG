"""Environment utility functions.

This module provides utility functions for handling environment variables and paths.
"""

import logging
import os
from pathlib import Path
from app.core.config import get_settings

logger = logging.getLogger(__name__)

# Required environment variables
REQUIRED_ENV_VARS = ["GOOGLE_API_KEY", "OPENAI_API_KEY"]


def get_env_file_path() -> Path:
    """Get the path to the .env file.

    Returns:
        Path: Path to the .env file.
    """
    return Path(__file__).parent.parent.parent / ".env"


def validate_env_vars() -> list[str]:
    """Validate that all required environment variables are set.

    Returns:
        list[str]: List of missing environment variables.
    """
    missing_vars = []
    for var in REQUIRED_ENV_VARS:
        if not os.getenv(var):
            missing_vars.append(var)
    return missing_vars


def load_env(validate: bool = True) -> None:
    """Load environment variables from .env file.

    Args:
        validate: Whether to validate required environment variables.

    Raises:
        FileNotFoundError: If .env file doesn't exist.
        ValueError: If required environment variables are missing.
    """
    env_path = get_env_file_path()

    if not env_path.exists():
        raise FileNotFoundError(
            f".env file not found at {env_path}. "
            "Please copy .env.example to .env and configure your environment variables."
        )

    if validate:
        missing_vars = validate_env_vars()
        if missing_vars:
            raise ValueError(
                "Missing required environment variables: "
                f"{', '.join(missing_vars)}. "
                "Please check your .env file."
            )


def get_google_api_key() -> str:
    """Get the Google API key from environment variables.

    Returns:
        str: The Google API key.

    Raises:
        ValueError: If GOOGLE_API_KEY is not set.
    """
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY environment variable is not set. "
            "Please copy .env.example to .env and set your API key."
        )
    return api_key


def get_data_root() -> Path:
    """Get the data root directory.

    Returns:
        Path to the data root directory
    """
    settings = get_settings()
    return Path(settings.DATA_ROOT).expanduser()


def get_input_dir() -> Path:
    """Get the input directory.

    Returns:
        Path to the input directory
    """
    settings = get_settings()
    return Path(settings.INPUT_DIR).expanduser()


def get_output_dir() -> Path:
    """Get the output directory.

    Returns:
        Path to the output directory
    """
    settings = get_settings()
    return Path(settings.OUTPUT_DIR).expanduser()


def get_chroma_dir() -> Path:
    """Get the ChromaDB directory.

    Returns:
        Path to the ChromaDB directory
    """
    settings = get_settings()
    return Path(settings.CHROMA_DATA_DIR).expanduser()


def get_chunks_dir() -> Path:
    """Get the chunks directory.

    Returns:
        Path to the chunks directory
    """
    settings = get_settings()
    return Path(settings.CHUNKS_DIR).expanduser()


def get_tenant_root() -> Path:
    """Get the tenant root directory.

    Returns:
        Path to the tenant root directory
    """
    settings = get_settings()
    return Path(settings.TENANT_ROOT)


def get_cache_dir() -> Path:
    """Get the cache directory.

    Returns:
        Path to the cache directory
    """
    settings = get_settings()
    return Path(settings.CACHE_DIR)


def get_docs_root() -> Path:
    """Get the path to the documents root directory.

    Returns:
        Path: The path to the documents root directory.
    """
    settings = get_settings()
    docs_root = settings.DOCS_ROOT
    return Path(docs_root)


def ensure_directories() -> None:
    """Ensure all required directories exist.

    Creates any missing directories that are required for the application to function.
    """
    directories = [
        get_data_root(),
        get_input_dir(),
        get_output_dir(),
        get_chroma_dir(),
        get_chunks_dir(),
        get_tenant_root(),
        get_cache_dir(),
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
