"""Authentication module for API security.

This module provides authentication middleware and secret management
functions for securing the API endpoints.
"""

import logging
import os
from typing import Optional, Callable, Awaitable

from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
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
        Otherwise, try to load it from environment or Secret Manager.

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

        # Try to get token from environment first
        token = os.getenv("API_TOKEN")
        if token:
            cls._token = token
            return token

        # Otherwise, get the token from GCP Secret Manager
        try:
            # Import here to avoid issues during testing
            from google.cloud import secretmanager

            # Get configuration from settings
            project_id = settings.GCP_PROJECT_ID
            secret_name = settings.GCP_SECRET_NAME
            secret_version = settings.GCP_SECRET_VERSION

            # Build the secret path from configuration
            secret_path = (
                f"projects/{project_id}/secrets/{secret_name}/versions/{secret_version}"
            )
            logger.debug(f"Using secret path: {secret_path}")

            # Create the Secret Manager client
            client = secretmanager.SecretManagerServiceClient()

            # Access the secret version
            response = client.access_secret_version(request={"name": secret_path})

            # Extract the payload as a string
            token = response.payload.data.decode("UTF-8")
            cls._token = token

            return token
        except Exception as e:
            logger.error(f"Error retrieving token from Secret Manager: {e}")
            raise Exception("Failed to retrieve authentication token") from e

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

        project_id = settings.GCP_PROJECT_ID
        secret_name = settings.GCP_SECRET_NAME

        # Create the Secret Manager client
        client = secretmanager.SecretManagerServiceClient()

        # Build the parent resource name
        parent = f"projects/{project_id}"

        # Check if the secret already exists
        secret_path = f"{parent}/secrets/{secret_name}"
        try:
            client.get_secret(request={"name": secret_path})
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
                "parent": secret_path,
                "payload": {"data": token.encode("UTF-8")},
            }
        )

        return token
    except Exception as e:
        logger.error(f"Error storing token in Secret Manager: {e}")
        raise Exception("Failed to store authentication token") from e
