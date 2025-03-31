"""Utility functions for the Legal Search RAG application."""

# Import common utilities
import logging

# Conditionally import GCP storage utilities
import os

from app.utils.env import (
    get_chroma_dir,
    get_chunks_dir,
    get_docs_root,
    get_env_file_path,
    get_google_api_key,
    get_input_dir,
    get_output_dir,
    is_gcp_configured,
    load_env,
    validate_env_vars,
)
from app.utils.token_counter import count_tokens, estimate_tokens_and_cost, format_cost
from app.utils.usage_db import (
    check_quota_exceeded,
    get_daily_usage,
    get_monthly_usage,
    get_quota_info,
    init_usage_db,
    record_usage,
    reset_usage_data,
    update_quota_settings,
)

logger = logging.getLogger(__name__)
GCP_AVAILABLE = False

if os.getenv("USE_GCP_STORAGE", "false").lower() == "true":
    try:
        from utils.gcp_storage import (
            download_file,
            file_exists,
            get_file_content,
            init_storage_client,
            list_files,
            upload_file,
        )

        GCP_AVAILABLE = True
        logger.info("GCP storage utilities imported successfully")
    except ImportError as e:
        logger.warning(f"Could not import GCP storage utilities: {e}")

        # Provide dummy implementations for GCP storage functions
        def upload_file(*args, **kwargs):
            return False, "GCP storage not available"

        def download_file(*args, **kwargs):
            return False, "GCP storage not available"

        def list_files(*args, **kwargs):
            return []

        def file_exists(*args, **kwargs):
            return False

        def get_file_content(*args, **kwargs):
            return False, None

        def init_storage_client(*args, **kwargs):
            return None
else:
    logger.info("GCP storage disabled in config - using local storage only")

    # Provide dummy implementations for GCP storage functions
    def upload_file(*args, **kwargs):
        return False, "GCP storage not available"

    def download_file(*args, **kwargs):
        return False, "GCP storage not available"

    def list_files(*args, **kwargs):
        return []

    def file_exists(*args, **kwargs):
        return False

    def get_file_content(*args, **kwargs):
        return False, None

    def init_storage_client(*args, **kwargs):
        return None


__all__ = [
    "count_tokens",
    "estimate_tokens_and_cost",
    "format_cost",
    "init_usage_db",
    "record_usage",
    "get_monthly_usage",
    "get_quota_info",
    # GCP Storage utilities
    "upload_file",
    "download_file",
    "list_files",
    "file_exists",
    "get_file_content",
    "init_storage_client",
    "GCP_AVAILABLE",
]
