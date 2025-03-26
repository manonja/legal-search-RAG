"""Environment variable utilities for configuration management."""

import logging
import os
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Required environment variables
REQUIRED_ENV_VARS = ["GOOGLE_API_KEY", "OPENAI_API_KEY"]


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


def get_docs_root() -> Path:
    """Get the root directory for document storage.

    Returns:
        Path: Expanded absolute path to the docs root directory
    """
    docs_root = os.getenv("DOCS_ROOT")

    if not docs_root:
        # Default to a documents directory in the user's home
        docs_root = os.path.expanduser("~/Downloads/legaldocs_store")
    else:
        # Expand user and environment variables
        docs_root = os.path.expanduser(docs_root)

    # Create the directory if it doesn't exist
    os.makedirs(docs_root, exist_ok=True)

    return Path(docs_root)


def get_input_dir() -> Path:
    """Get the input directory for raw document files.

    Returns:
        Path: Expanded absolute path to the input directory
    """
    input_dir = os.getenv("INPUT_DIR")

    if not input_dir:
        # Default to a subdirectory within the docs root
        input_dir = os.path.expanduser("~/Downloads/legaldocs_input")
    else:
        # Expand user and environment variables
        input_dir = os.path.expanduser(input_dir)

    # Create the directory if it doesn't exist
    os.makedirs(input_dir, exist_ok=True)

    return Path(input_dir)


def get_output_dir() -> Path:
    """Get the output directory for processed documents.

    Returns:
        Path: Expanded absolute path to the output directory
    """
    output_dir = os.getenv("OUTPUT_DIR")

    if not output_dir:
        # Default to a subdirectory within the docs root
        output_dir = os.path.expanduser("~/Downloads/legaldocs_processed")
    else:
        # Expand user and environment variables
        output_dir = os.path.expanduser(output_dir)

    # Create the directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    return Path(output_dir)


def get_chunks_dir() -> Path:
    """Get the directory where chunked documents are stored.

    Returns:
        Path to the chunked documents directory
    """
    chunks_dir = os.getenv(
        "CHUNKS_DIR", os.path.expanduser("~/Downloads/legaldocs_chunks")
    )

    # Create directory if it doesn't exist
    os.makedirs(chunks_dir, exist_ok=True)

    logger.info(f"Using chunks directory: {chunks_dir}")
    return Path(chunks_dir)


def get_chroma_dir() -> Path:
    """Get the ChromaDB data directory.

    Returns:
        Path to the ChromaDB data directory
    """
    chroma_dir = os.getenv(
        "CHROMA_DATA_DIR", os.path.expanduser("~/Downloads/legal_chroma")
    )

    # Create directory if it doesn't exist
    os.makedirs(chroma_dir, exist_ok=True)

    logger.info(f"Using ChromaDB directory: {chroma_dir}")
    return Path(chroma_dir)


# Function to indicate GCP is not configured for local dev
def is_gcp_configured():
    """Check if GCP is configured in the environment."""
    return False
