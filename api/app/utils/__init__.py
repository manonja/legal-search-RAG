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

__all__ = [
    "count_tokens",
    "estimate_tokens_and_cost",
    "format_cost",
    "init_usage_db",
    "record_usage",
    "get_monthly_usage",
    "get_quota_info",
]
