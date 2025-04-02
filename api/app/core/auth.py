"""Authentication module for API security.

This module provides authentication middleware and security functions
for securing the API endpoints.
"""

import logging
import os
import warnings
from typing import Awaitable, Callable, Optional

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import get_settings

# Configure logging
logger = logging.getLogger(__name__)

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

        If the token is already loaded, return it.
        Otherwise, try to load it from environment, settings, or Secret Manager.

        Returns:
            str: The API token

        Raises:
            Exception: If token couldn't be retrieved
        """
        # If the token is already loaded, return it
        if cls._token:
            return cls._token

        # For tests, try to get token from environment
        if os.getenv("TESTING") == "true":
            token = os.getenv("API_TOKEN") or "test-token"
            cls._token = token
            return token

        # Try to get token from settings or environment
        token = settings.API_TOKEN or os.getenv("API_TOKEN")
        if token:
            cls._token = token
            return token

        # Otherwise, get the token from GCP Secret Manager
        # Import here to avoid issues during testing
        from google.cloud import secretmanager

        if not settings.API_TOKEN_SECRET_NAME:
            warnings.warn(
                "API_TOKEN_SECRET_NAME is not set, using default token",
                UserWarning,
                stacklevel=2,
            )
            cls._token = "test-token"  # noqa: S105
            return cls._token

        # Use the full secret path directly
        secret_path = settings.API_TOKEN_SECRET_NAME
        logger.debug(f"Using secret path: {secret_path}")

        # Create the Secret Manager client
        client = secretmanager.SecretManagerServiceClient()

        # Access the secret version
        response = client.access_secret_version(request={"name": secret_path})

        # Extract the payload as a string
        token = response.payload.data.decode("UTF-8")
        cls._token = token

        return token

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
    """Generate a new API token and store it in Secret Manager.

    Returns:
        str: The generated token

    Raises:
        Exception: If token couldn't be stored
    """
    import secrets

    # Generate a secure random token
    token = secrets.token_hex(32)

    # Don't try to store the token in Secret Manager in test mode
    if os.getenv("TESTING") == "true":
        return token

    # Store the token in Secret Manager
    try:
        # Import here to avoid issues during testing
        from google.cloud import secretmanager

        # For token generation, we expect a simpler secret name
        # (not the full path with version)
        secret_path = settings.API_TOKEN_SECRET_NAME
        logger.debug(f"Using secret path for storage: {secret_path}")

        # Create the Secret Manager client
        client = secretmanager.SecretManagerServiceClient()

        # If secret_path is a full path, we need to extract the parent and secret name
        if secret_path.startswith("projects/") and "/secrets/" in secret_path:
            # Extract the parent part (everything up to /secrets/)
            parent = secret_path.split("/secrets/")[0]

            # Extract the secret name (between /secrets/ and /versions/ if present)
            secret_parts = secret_path.split("/secrets/")[1].split("/versions/")
            secret_name = secret_parts[0]
        else:
            # Default case: use GCP project ID and the whole path as secret name
            parent = f"projects/{settings.GCP_PROJECT_ID}"
            secret_name = secret_path

        # Check if the secret already exists
        full_secret_path = f"{parent}/secrets/{secret_name}"
        try:
            client.get_secret(request={"name": full_secret_path})
            secret_exists = True
        except Exception:
            secret_exists = False

        # Create the secret if it doesn't exist
        if not secret_exists:
            client.create_secret(
                request={
                    "parent": parent,
                    "secret_id": secret_name,
                    "secret": {"replication": {"automatic": {}}},
                }
            )

        # Add the new secret version
        client.add_secret_version(
            request={
                "parent": full_secret_path,
                "payload": {"data": token.encode("UTF-8")},
            }
        )

        return token
    except Exception as e:
        logger.error(f"Error storing token in Secret Manager: {e}")
        raise Exception("Failed to store authentication token") from e


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
