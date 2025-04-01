"""Utility functions for the Legal Search RAG application."""

# Import common utilities
import logging

from app.utils.env import (
    get_chroma_dir,
    get_chunks_dir,
    get_docs_root,
    get_env_file_path,
    get_google_api_key,
    get_input_dir,
    get_output_dir,
    load_env,
    validate_env_vars,
)

logger = logging.getLogger(__name__)

__all__ = []
