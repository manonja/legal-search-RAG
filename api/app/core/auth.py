"""Authentication module for API security.

This module provides authentication middleware and security functions
for securing the API endpoints.
"""

import os
import warnings
from typing import Awaitable, Callable, Optional

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from app.core.struct_logger import log

from app.core.config import get_settings

# Initialize settings
settings = get_settings()

# Create security scheme for Swagger UI, disable auto_error for 401
security = HTTPBearer(auto_error=False, description="API token authentication")


class TokenManager:
    """Token Manager for retrieving and validating API tokens."""

    _token: Optional[str] = None

    @classmethod
    async def get_token(cls) -> str:
        """Get the API authentication token.

        Returns:
            str: The API token

        Raises:
            ValueError: If token is missing in production
        """
        # Return cached token if available
        if cls._token:
            return cls._token

        # Handle testing environment
        if os.getenv("TESTING") == "true":
            cls._token = os.getenv("API_TOKEN") or "test-token"
            return cls._token

        # Try to get token from configured sources
        token = settings.API_TOKEN or os.getenv("API_TOKEN")
        if token:
            cls._token = token
            return token

        # No token found - decide what to do based on environment
        if settings.DEBUG or not settings.is_production:
            warnings.warn(
                "API_TOKEN environment variable is not set, using default token - NOT SECURE FOR PRODUCTION",
                UserWarning,
                stacklevel=2,
            )
            cls._token = "test-token"  # noqa: S105
        else:
            error_msg = "API_TOKEN environment variable is not set in production mode"
            log.error(error_msg)
            raise ValueError(error_msg)

        return cls._token

    @classmethod
    async def verify_token(cls, token: str) -> bool:
        """Verify if the provided token is valid.

        Args:
            token: The token to verify

        Returns:
            bool: True if token is valid, False otherwise
        """
        if os.getenv("TESTING") == "true":
            # In testing environment, accept any token
            return True

        # Get the expected token
        expected_token = await cls.get_token()

        # Verify token
        return token == expected_token


async def generate_and_store_token() -> str:
    """Generate a new API token.

    Returns:
        str: The generated token
    """
    import secrets

    # Generate a secure random token
    token = secrets.token_hex(32)

    # Log the token generation (don't log the token itself)
    log.info("Generated new API token")

    return token


class AuthMiddleware(BaseHTTPMiddleware):
    """Middleware for authentication handling."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process the request through the middleware.

        Args:
            request: The incoming request
            call_next: The next middleware or route handler

        Returns:
            The response from the next handler
        """
        # Skip authentication for health check and docs endpoints
        path = request.url.path
        if (
            path.startswith(f"{settings.API_PREFIX}/health")
            and not path.endswith("/auth-test")
            or path.startswith(f"{settings.API_PREFIX}/docs")
            or path.startswith(f"{settings.API_PREFIX}/redoc")
            or path.startswith(f"{settings.API_PREFIX}/openapi.json")
        ):
            return await call_next(request)

        # Skip authentication in testing mode
        if os.getenv("TESTING") == "true":
            return await call_next(request)

        # Get authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header is missing",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if it's a Bearer token
        scheme, _, token = auth_header.partition(" ")
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization scheme must be Bearer",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Verify token
        if not await TokenManager.verify_token(token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Continue with the request
        return await call_next(request)
