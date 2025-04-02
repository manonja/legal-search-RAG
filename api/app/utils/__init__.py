"""Utility functions for the Legal Search RAG application."""

# Import common utilities
import logging
from app.core.config import get_settings

logger = logging.getLogger(__name__)


# Create aliased functions for backward compatibility
def get_chroma_dir():
    """Get the ChromaDB directory.

    Returns:
        Path to the ChromaDB directory
    """
    return get_settings().chroma_dir_path


def get_chunks_dir():
    """Get the chunks directory.

    Returns:
        Path to the chunks directory
    """
    return get_settings().chunks_dir_path


def get_data_root():
    """Get the data root directory.

    Returns:
        Path to the data root directory
    """
    return get_settings().data_root_path


def get_env_file_path():
    """Get the path to the .env file.

    Returns:
        Path: Path to the .env file.
    """
    return get_settings().get_env_file_path()


def get_google_api_key():
    """Get the Google API key.

    Returns:
        str: The Google API key.
    """
    return get_settings().get_google_api_key()


def get_input_dir():
    """Get the input directory.

    Returns:
        Path to the input directory
    """
    return get_settings().input_dir_path


def get_output_dir():
    """Get the output directory.

    Returns:
        Path to the output directory
    """
    return get_settings().output_dir_path


def get_docs_root():
    """Get the path to the documents root directory.

    Returns:
        Path: The path to the documents root directory.
    """
    return get_settings().docs_root_path


def get_cache_dir():
    """Get the cache directory.

    Returns:
        Path to the cache directory
    """
    return get_settings().cache_dir_path


def get_tenant_root():
    """Get the tenant root directory.

    Returns:
        Path to the tenant root directory
    """
    return get_settings().tenant_root_path


def load_env(validate=True):
    """Load environment variables from .env file.

    Args:
        validate: Whether to validate required environment variables.
    """
    get_settings().load_env(validate)


def validate_env_vars():
    """Validate that all required environment variables are set.

    Returns:
        list[str]: List of missing environment variables.
    """
    return get_settings().validate_env_vars()


def ensure_directories():
    """Ensure all required directories exist."""
    get_settings().ensure_directories()


__all__ = [
    "get_chroma_dir",
    "get_chunks_dir",
    "get_data_root",
    "get_env_file_path",
    "get_google_api_key",
    "get_input_dir",
    "get_output_dir",
    "get_docs_root",
    "get_cache_dir",
    "get_tenant_root",
    "load_env",
    "validate_env_vars",
    "ensure_directories",
]
