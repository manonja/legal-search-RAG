"""Health check router.

This module provides endpoints for checking the health status of the API.
"""

from fastapi import APIRouter
from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Check if the API is healthy."""
    settings = get_settings()
    return {"status": "ok", "version": settings.API_VERSION}
