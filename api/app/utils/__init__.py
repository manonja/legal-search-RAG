"""Utility functions for the Legal Search RAG application."""

# Import common utilities
import logging

from app.utils.env import (
    get_chroma_dir,
    get_chunks_dir,
    get_data_root,
    get_env_file_path,
    get_google_api_key,
    get_input_dir,
    get_output_dir,
    load_env,
    validate_env_vars,
    get_tenant_root,
    get_cache_dir,
    ensure_directories,
)

logger = logging.getLogger(__name__)

__all__ = [
    "get_chroma_dir",
    "get_chunks_dir",
    "get_data_root",
    "get_input_dir",
    "get_output_dir",
    "get_tenant_root",
    "get_cache_dir",
    "ensure_directories",
]
