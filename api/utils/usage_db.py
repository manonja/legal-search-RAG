"""Simplified usage tracking for local development.

This module provides dummy implementations of the usage tracking functions
to ensure the API can run without a full usage database setup.
"""

import logging
import os
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


def init_usage_db():
    """Initialize the usage database.

    In local development mode, this is a no-op.
    """
    logger.info("Initializing dummy usage database for local development")
    # Create cache directory
    cache_dir = Path(os.path.expanduser("~/Downloads/legal_cache"))
    cache_dir.mkdir(exist_ok=True, parents=True)
    return True


def record_usage(query_type, tokens_used, model_name="gpt-3.5-turbo", cost=0.0):
    """Record API usage.

    In local development mode, this only logs the usage.

    Args:
        query_type: Type of query (search, rag-search)
        tokens_used: Number of tokens used
        model_name: Model used for the query
        cost: Estimated cost of the query
    """
    logger.info(
        f"Usage recorded: {query_type}, {tokens_used} tokens, "
        f"model: {model_name}, cost: ${cost:.6f}"
    )

    # In a real implementation, we would save this to a database
    # For local development, we'll just append to a log file
    try:
        log_file = Path(os.path.expanduser("~/Downloads/legal_cache/usage_log.txt"))
        with open(log_file, "a") as f:
            timestamp = datetime.now().isoformat()
            f.write(f"{timestamp}|{query_type}|{tokens_used}|{model_name}|{cost:.6f}\n")
    except Exception as e:
        logger.error(f"Error writing to usage log: {e}")

    return True


def get_quota_info():
    """Get quota information.

    Returns:
        Dictionary with default quota settings.
    """
    return {
        "monthly_budget": float(os.getenv("OPENAI_MONTHLY_BUDGET", 30.0)),
        "max_queries_per_month": int(os.getenv("MAX_QUERIES_PER_MONTH", 100)),
        "cost_warning_threshold": 0.10,
    }


def check_quota_exceeded():
    """Check if the quota has been exceeded.

    In local development mode, the quota is never exceeded.

    Returns:
        Tuple of (exceeded, reason)
    """
    return False, ""


def get_monthly_usage(year, month):
    """Get usage statistics for a specific month.

    Returns:
        Dictionary with default usage statistics.
    """
    return {
        "query_count": 0,
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "total_tokens": 0,
        "total_cost": 0.0,
        "budget_percent": 0.0,
        "query_percent": 0.0,
        "models_usage": [],
        "year": year,
        "month": month,
    }


def update_quota_settings(**kwargs):
    """Update quota settings.

    In local development mode, this is a no-op.
    """
    logger.info(f"Updating quota settings: {kwargs}")
    return True


def reset_usage_data():
    """Reset all usage data.

    In local development mode, this is a no-op.
    """
    logger.info("Resetting usage data")
    try:
        log_file = Path(os.path.expanduser("~/Downloads/legal_cache/usage_log.txt"))
        if log_file.exists():
            log_file.unlink()
    except Exception as e:
        logger.error(f"Error resetting usage data: {e}")
    return True


def get_daily_usage(year, month):
    """Get daily usage statistics for a specific month.

    Returns:
        List of dictionaries with daily usage.
    """
    return []
