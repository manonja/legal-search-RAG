"""Environment variable utilities for configuration management."""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Required environment variables
REQUIRED_ENV_VARS = ["GOOGLE_API_KEY", "DOCS_ROOT"]


def get_env_file_path() -> Path:
    """Get the path to the .env file.

    Returns:
        Path: Path to the .env file.
    """
    return Path(__file__).parent.parent / ".env"


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

    load_dotenv(env_path)

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


def get_input_dir() -> str:
    """Get the input directory from environment variables or default.

    Returns:
        str: The input directory path.
    """
    return os.getenv("INPUT_DIR", os.path.expanduser("~/Downloads/legaldocs"))


def get_output_dir() -> str:
    """Get the output directory from environment variables or default.

    Returns:
        str: The output directory path.
    """
    return os.getenv("OUTPUT_DIR", os.path.expanduser("~/Downloads/processedLegalDocs"))


def get_docs_root() -> str:
    """Get the root directory for legal documents.

    Returns:
        Path to the documents directory
    """
    docs_root = os.getenv("DOCS_ROOT", os.path.expanduser("~/Downloads/legalDocs"))
    logger.info(f"Using documents root: {docs_root}")

    # Create directory if it doesn't exist
    os.makedirs(docs_root, exist_ok=True)

    return docs_root


def get_chunks_dir() -> str:
    """Get the directory where chunked documents are stored.

    Returns:
        Path to the chunked documents directory
    """
    chunks_dir = os.getenv(
        "CHUNKS_DIR", os.path.expanduser("~/Downloads/chunkedLegalDocs")
    )
    logger.info(f"Using chunks directory: {chunks_dir}")

    # Create directory if it doesn't exist
    os.makedirs(chunks_dir, exist_ok=True)

    return chunks_dir
