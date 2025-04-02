"""Health check router.

This module provides endpoints for checking the health status of the API.
"""

import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials

from app.core.config import get_settings
from app.core.auth import security, TokenManager

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Check if the API is healthy."""
    settings = get_settings()
    return {"status": "ok", "version": settings.API_VERSION}


async def auth_dependency(request: Request):
    """Authentication dependency that respects test mode.

    This resolves the security dependency internally to avoid Ruff B008.

    Args:
        request: The incoming request object.

    Returns:
        str: The token if valid

    Raises:
        HTTPException: If authentication fails
    """
    # In test mode, bypass authentication
    if os.getenv("TESTING") == "true":
        return "test-token"

    # Manually invoke the security dependency callable
    # security is an instance of HTTPBearer(auto_error=False)
    credentials: Optional[HTTPAuthorizationCredentials] = await security(request)

    # If auto_error=False, credentials might be None
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract token
    token = credentials.credentials

    # Verify token
    is_valid = await TokenManager.verify_token(token)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return token


@router.get("/health/auth-test")
async def auth_test(token: str = Depends(auth_dependency)):
    """Test endpoint that requires authentication."""
    return {"status": "authenticated", "message": "Authentication successful"}
