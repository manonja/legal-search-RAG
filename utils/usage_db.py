"""SQLite-based usage tracking database for the OpenAI API."""

import logging
import os
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

# Get tenant ID from environment variable, default to 'default'
TENANT_ID = os.getenv("TENANT_ID", "default")

# Path to SQLite database file - now tenant-specific
DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "cache", f"usage_{TENANT_ID}.db"
)


def init_usage_db() -> None:
    """Initialize the usage tracking database.

    Creates the database file and tables if they don't already exist.
    """
    # Create parent directory if it doesn't exist
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    logger.info(f"Initializing usage database for tenant {TENANT_ID} at {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create the API usage tracking table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS api_usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        conversation_id TEXT,
        query TEXT NOT NULL,
        model TEXT NOT NULL,
        input_tokens INTEGER NOT NULL,
        output_tokens INTEGER NOT NULL,
        total_tokens INTEGER NOT NULL,
        cost REAL NOT NULL
    )
    """
    )

    # Create the quota settings table
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS quota_settings (
        id INTEGER PRIMARY KEY,
        monthly_budget REAL NOT NULL,
        max_queries_per_month INTEGER NOT NULL,
        cost_warning_threshold REAL NOT NULL,
        updated_at TEXT NOT NULL
    )
    """
    )

    # Insert default quota settings if none exist
    cursor.execute("SELECT COUNT(*) FROM quota_settings")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            """INSERT INTO quota_settings
            (monthly_budget, max_queries_per_month, cost_warning_threshold, updated_at)
            VALUES (?, ?, ?, ?)""",
            (30.0, 100, 0.10, datetime.now().isoformat()),
        )

    conn.commit()
    conn.close()

    logger.info(f"Usage tracking database initialized at {DB_PATH}")


def log_api_usage(
    query: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    total_tokens: int,
    cost: float,
    conversation_id: Optional[str] = None,
) -> int:
    """Log an API usage record to the database.

    Args:
        query: The user's query
        model: The model used for the response
        input_tokens: Number of input tokens used
        output_tokens: Number of output tokens used
        total_tokens: Total tokens used
        cost: Estimated cost in USD
        conversation_id: Optional conversation ID for tracking contexts

    Returns:
        ID of the inserted record
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    timestamp = datetime.now().isoformat()

    cursor.execute(
        """INSERT INTO api_usage
        (timestamp, conversation_id, query, model, input_tokens, output_tokens, total_tokens, cost)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            timestamp,
            conversation_id,
            query,
            model,
            input_tokens,
            output_tokens,
            total_tokens,
            cost,
        ),
    )

    last_id = cursor.lastrowid
    conn.commit()
    conn.close()

    logger.debug(f"Logged API usage: {model}, {total_tokens} tokens, ${cost:.6f}")
    return last_id  # type: ignore


def get_monthly_usage(
    year: Optional[int] = None, month: Optional[int] = None
) -> Dict[str, Union[int, float]]:
    """Get usage statistics for a specific month.

    Args:
        year: Year to check (defaults to current year)
        month: Month to check (defaults to current month)

    Returns:
        Dictionary with usage statistics
    """
    if year is None or month is None:
        now = datetime.now()
        year = now.year if year is None else year
        month = now.month if month is None else month

    # Create date range for the month
    start_date = f"{year}-{month:02d}-01"
    if month == 12:
        end_date = f"{year + 1}-01-01"
    else:
        end_date = f"{year}-{month + 1:02d}-01"

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get aggregate usage for the month
    cursor.execute(
        """
        SELECT
            COUNT(*) as query_count,
            SUM(input_tokens) as total_input_tokens,
            SUM(output_tokens) as total_output_tokens,
            SUM(total_tokens) as total_tokens,
            SUM(cost) as total_cost
        FROM api_usage
        WHERE timestamp >= ? AND timestamp < ?
    """,
        (start_date, end_date),
    )

    row = cursor.fetchone()

    # Get usage by model
    cursor.execute(
        """
        SELECT
            model,
            COUNT(*) as query_count,
            SUM(total_tokens) as total_tokens,
            SUM(cost) as total_cost
        FROM api_usage
        WHERE timestamp >= ? AND timestamp < ?
        GROUP BY model
    """,
        (start_date, end_date),
    )

    models_usage = []
    for model_row in cursor.fetchall():
        models_usage.append(
            {
                "model": model_row[0],
                "query_count": model_row[1],
                "total_tokens": model_row[2],
                "total_cost": model_row[3],
            }
        )

    conn.close()

    # Get quota settings
    quota = get_quota_info()

    return {
        "query_count": row[0] if row[0] else 0,
        "total_input_tokens": row[1] if row[1] else 0,
        "total_output_tokens": row[2] if row[2] else 0,
        "total_tokens": row[3] if row[3] else 0,
        "total_cost": row[4] if row[4] else 0.0,
        "budget_percent": (
            (row[4] / quota["monthly_budget"]) * 100
            if row[4] and quota["monthly_budget"] > 0
            else 0
        ),
        "query_percent": (
            (row[0] / quota["max_queries_per_month"]) * 100
            if row[0] and quota["max_queries_per_month"] > 0
            else 0
        ),
        "models_usage": models_usage,
        "year": year,
        "month": month,
    }


def get_quota_info() -> Dict[str, Union[float, int]]:
    """Get the current quota settings.

    Returns:
        Dictionary with quota settings
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT monthly_budget, max_queries_per_month, cost_warning_threshold FROM quota_settings WHERE id = 1"
    )
    row = cursor.fetchone()

    conn.close()

    # Use environment variables for default values if DB record not found
    if not row:
        return {
            "monthly_budget": float(os.getenv("OPENAI_MONTHLY_BUDGET", "30.0")),
            "max_queries_per_month": int(os.getenv("MAX_QUERIES_PER_MONTH", "100")),
            "cost_warning_threshold": 0.10,
        }

    return {
        "monthly_budget": row[0],
        "max_queries_per_month": row[1],
        "cost_warning_threshold": row[2],
    }


def update_quota_settings(
    monthly_budget: Optional[float] = None,
    max_queries_per_month: Optional[int] = None,
    cost_warning_threshold: Optional[float] = None,
) -> None:
    """Update quota settings in the database.

    Args:
        monthly_budget: New monthly budget in USD
        max_queries_per_month: New maximum queries per month
        cost_warning_threshold: New cost warning threshold
    """
    # Get current settings
    current = get_quota_info()

    # Update with new values if provided
    if monthly_budget is not None:
        current["monthly_budget"] = monthly_budget
    if max_queries_per_month is not None:
        current["max_queries_per_month"] = max_queries_per_month
    if cost_warning_threshold is not None:
        current["cost_warning_threshold"] = cost_warning_threshold

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE quota_settings SET monthly_budget = ?, max_queries_per_month = ?, cost_warning_threshold = ?, updated_at = ? WHERE id = 1",
        (
            current["monthly_budget"],
            current["max_queries_per_month"],
            current["cost_warning_threshold"],
            datetime.now().isoformat(),
        ),
    )

    conn.commit()
    conn.close()

    logger.info(
        f"Updated quota settings: ${current['monthly_budget']} monthly budget, {current['max_queries_per_month']} max queries"
    )


def check_quota_exceeded() -> Tuple[bool, str]:
    """Check if current usage has exceeded monthly quota.

    Returns:
        Tuple of (exceeded, reason) where exceeded is a boolean and
        reason is a string explaining which quota was exceeded
    """
    # Get current month's usage
    usage = get_monthly_usage()
    quota = get_quota_info()

    # Check cost quota
    if usage["total_cost"] >= quota["monthly_budget"]:
        return (
            True,
            f"Monthly budget of ${quota['monthly_budget']} exceeded (${usage['total_cost']:.2f} used)",
        )

    # Check query count quota
    if usage["query_count"] >= quota["max_queries_per_month"]:
        return (
            True,
            f"Monthly query limit of {quota['max_queries_per_month']} exceeded ({usage['query_count']} used)",
        )

    return (False, "")


def reset_usage_data() -> None:
    """Clear all usage data from the database.

    This is primarily used for testing or allowing manual resets.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM api_usage")

    conn.commit()
    conn.close()

    logger.warning("All usage data has been reset")


def get_daily_usage(year: int, month: int) -> List[Dict[str, Union[str, int, float]]]:
    """Get daily usage statistics for a specific month.

    Args:
        year: Year to get usage for
        month: Month to get usage for

    Returns:
        List of daily usage statistics with day, queries, tokens and cost
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get daily stats for the specified month
    cursor.execute(
        """
        SELECT
            strftime('%Y-%m-%d', timestamp) as day,
            COUNT(*) as query_count,
            SUM(total_tokens) as total_tokens,
            SUM(cost) as total_cost
        FROM api_usage
        WHERE strftime('%Y', timestamp) = ? AND strftime('%m', timestamp) = ?
        GROUP BY day
        ORDER BY day
        """,
        (str(year), f"{month:02d}"),
    )

    results = cursor.fetchall()
    conn.close()

    # Format the results
    daily_stats = []
    for day, query_count, total_tokens, total_cost in results:
        daily_stats.append(
            {
                "day": day,
                "queries": query_count,
                "tokens": total_tokens or 0,
                "cost": total_cost or 0,
            }
        )

    # Fill in missing days with zero values
    all_days = []

    # Initialize start and end dates
    start_date = datetime(year, month, 1)

    # If it's the current month, only go up to today
    current_date = datetime.now()
    if year == current_date.year and month == current_date.month:
        end_date = current_date
    else:
        # For past months, go to the end of the month
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

    # Generate date range
    current = start_date
    while current < end_date:
        day_str = current.strftime("%Y-%m-%d")

        # Check if this day exists in our results
        day_exists = False
        for stat in daily_stats:
            if stat["day"] == day_str:
                all_days.append(stat)
                day_exists = True
                break

        # If not, add a zero entry
        if not day_exists:
            all_days.append({"day": day_str, "queries": 0, "tokens": 0, "cost": 0})

        # Move to next day
        current = datetime(current.year, current.month, current.day + 1)

    return all_days
