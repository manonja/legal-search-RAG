"""Admin API endpoints for monitoring usage and managing cost settings."""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel

from utils.usage_db import (
    get_daily_usage,
    get_monthly_usage,
    get_quota_info,
    reset_usage_data,
    update_quota_settings,
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/admin", tags=["Admin"])

# API key security
API_KEY = os.getenv("ADMIN_API_KEY", "1234")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def get_api_key(api_key_header: str = Security(api_key_header)) -> str:
    """Validate API key for admin endpoints.

    Args:
        api_key_header: API key from request header

    Returns:
        Validated API key

    Raises:
        HTTPException: If API key is invalid
    """
    if not api_key_header or api_key_header != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return api_key_header


# API Models
class UsageResponse(BaseModel):
    """Usage statistics response model."""

    query_count: int
    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    total_cost: float
    budget_percent: float
    query_percent: float
    models_usage: List[Dict[str, Union[str, int, float]]]
    year: int
    month: int


class QuotaSettingsResponse(BaseModel):
    """Quota settings response model."""

    monthly_budget: float
    max_queries_per_month: int
    cost_warning_threshold: float


class QuotaUpdateRequest(BaseModel):
    """Request model for updating quota settings."""

    monthly_budget: Optional[float] = None
    max_queries_per_month: Optional[int] = None
    cost_warning_threshold: Optional[float] = None


class DailyUsage(BaseModel):
    """Daily usage data model."""

    day: str
    queries: int
    tokens: int
    cost: float


class UsageData(BaseModel):
    """Usage data model for dashboard."""

    month: str
    total_queries: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    total_cost: float
    daily_breakdown: List[DailyUsage]


class QuotaData(BaseModel):
    """Quota data model for dashboard."""

    limit: int
    used: int
    remaining: int
    percentage_used: float


class ThresholdData(BaseModel):
    """Threshold data model for dashboard."""

    per_query: float
    daily: float
    monthly: float


class MonthOverMonth(BaseModel):
    """Month over month comparison data."""

    queries: float
    tokens: float
    cost: float


class DashboardResponse(BaseModel):
    """Complete dashboard response."""

    current_usage: UsageData
    quota: QuotaData
    thresholds: ThresholdData
    previous_month: Optional[UsageData]
    month_over_month: MonthOverMonth
    projected_monthly_cost: float
    cost_per_query: float
    generated_at: str


# API Routes
@router.get("/usage", response_model=UsageResponse)
async def get_usage(
    year: Optional[int] = None,
    month: Optional[int] = None,
    api_key: str = Depends(get_api_key),
) -> UsageResponse:
    """Get usage statistics for a specific month.

    Args:
        year: Year to get usage for (defaults to current year)
        month: Month to get usage for (defaults to current month)
        api_key: API key for authorization

    Returns:
        Usage statistics
    """
    # Default to current month if not specified
    if not year or not month:
        now = datetime.now()
        year = year or now.year
        month = month or now.month

    # Get usage statistics
    usage = get_monthly_usage(year, month)
    return UsageResponse(**usage)


@router.get("/quota", response_model=QuotaSettingsResponse)
async def get_quota(api_key: str = Depends(get_api_key)) -> QuotaSettingsResponse:
    """Get current quota settings.

    Args:
        api_key: API key for authorization

    Returns:
        Current quota settings
    """
    quota = get_quota_info()
    return QuotaSettingsResponse(**quota)


@router.post("/quota", response_model=QuotaSettingsResponse)
async def update_quota(
    settings: QuotaUpdateRequest, api_key: str = Depends(get_api_key)
) -> QuotaSettingsResponse:
    """Update quota settings.

    Args:
        settings: New quota settings
        api_key: API key for authorization

    Returns:
        Updated quota settings
    """
    # Update settings
    update_quota_settings(
        monthly_budget=settings.monthly_budget,
        max_queries_per_month=settings.max_queries_per_month,
        cost_warning_threshold=settings.cost_warning_threshold,
    )

    # Return updated settings
    return QuotaSettingsResponse(**get_quota_info())


@router.post("/reset-usage")
async def reset_usage(api_key: str = Depends(get_api_key)) -> Dict[str, str]:
    """Reset all usage data.

    This endpoint is primarily for testing or administrative purposes.

    Args:
        api_key: API key for authorization

    Returns:
        Confirmation message
    """
    reset_usage_data()
    logger.warning("Usage data has been reset via admin API")
    return {"message": "Usage data has been reset successfully"}


@router.get("/dashboard", response_model=Dict[str, DashboardResponse])
async def get_dashboard(
    api_key: str = Depends(get_api_key),
) -> Dict[str, DashboardResponse]:
    """Get dashboard data combining usage, quota, and other statistics.

    Args:
        api_key: API key for authorization

    Returns:
        Dashboard data including current and past usage, projections, and quotas
    """
    # Get current date for reference
    now = datetime.now()
    current_year = now.year
    current_month = now.month

    # Get current month stats
    current_month_stats = get_monthly_usage(current_year, current_month)

    # Get previous month for comparison
    if current_month == 1:
        prev_month = 12
        prev_year = current_year - 1
    else:
        prev_month = current_month - 1
        prev_year = current_year

    # Try to get previous month stats, default to empty if not available
    try:
        prev_month_stats = get_monthly_usage(prev_year, prev_month)
    except Exception:
        # Default to empty stats if previous month has no data
        prev_month_stats = {
            "query_count": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_tokens": 0,
            "total_cost": 0,
            "budget_percent": 0,
            "query_percent": 0,
            "models_usage": [],
            "year": prev_year,
            "month": prev_month,
        }

    # Get quota info
    quota_info = get_quota_info()

    # Get daily breakdown for current month
    daily_usage = get_daily_usage(current_year, current_month)

    # Calculate days passed in current month
    days_passed = now.day
    days_in_month = (
        now.replace(month=current_month % 12 + 1, day=1) - timedelta(days=1)
    ).day

    # Calculate projections
    daily_avg_cost = current_month_stats["total_cost"] / max(days_passed, 1)
    projected_cost = daily_avg_cost * days_in_month

    # Calculate cost per query
    cost_per_query = 0
    if current_month_stats["query_count"] > 0:
        cost_per_query = (
            current_month_stats["total_cost"] / current_month_stats["query_count"]
        )

    # Calculate month over month changes (as percentages)
    month_over_month = {"queries": 0, "tokens": 0, "cost": 0}

    if prev_month_stats["query_count"] > 0:
        month_over_month["queries"] = (
            (current_month_stats["query_count"] - prev_month_stats["query_count"])
            / prev_month_stats["query_count"]
        ) * 100

    if prev_month_stats["total_tokens"] > 0:
        month_over_month["tokens"] = (
            (current_month_stats["total_tokens"] - prev_month_stats["total_tokens"])
            / prev_month_stats["total_tokens"]
        ) * 100

    if prev_month_stats["total_cost"] > 0:
        month_over_month["cost"] = (
            (current_month_stats["total_cost"] - prev_month_stats["total_cost"])
            / prev_month_stats["total_cost"]
        ) * 100

    # Format response data
    dashboard_data = {
        "current_usage": {
            "month": f"{current_year}-{current_month:02d}",
            "total_queries": current_month_stats["query_count"],
            "input_tokens": current_month_stats["total_input_tokens"],
            "output_tokens": current_month_stats["total_output_tokens"],
            "total_tokens": current_month_stats["total_tokens"],
            "total_cost": current_month_stats["total_cost"],
            "daily_breakdown": daily_usage,
        },
        "quota": {
            "limit": quota_info["max_queries_per_month"],
            "used": current_month_stats["query_count"],
            "remaining": max(
                0,
                quota_info["max_queries_per_month"]
                - current_month_stats["query_count"],
            ),
            "percentage_used": min(
                100,
                (
                    current_month_stats["query_count"]
                    / max(1, quota_info["max_queries_per_month"])
                )
                * 100,
            ),
        },
        "thresholds": {
            "per_query": quota_info["cost_warning_threshold"],
            "daily": quota_info["monthly_budget"] / 30,  # Approximation
            "monthly": quota_info["monthly_budget"],
        },
        "previous_month": {
            "month": f"{prev_year}-{prev_month:02d}",
            "total_queries": prev_month_stats["query_count"],
            "input_tokens": prev_month_stats["total_input_tokens"],
            "output_tokens": prev_month_stats["total_output_tokens"],
            "total_tokens": prev_month_stats["total_tokens"],
            "total_cost": prev_month_stats["total_cost"],
            "daily_breakdown": [],  # We don't need daily breakdown for previous month
        },
        "month_over_month": month_over_month,
        "projected_monthly_cost": projected_cost,
        "cost_per_query": cost_per_query,
        "generated_at": now.isoformat(),
    }

    return {"data": DashboardResponse(**dashboard_data)}
