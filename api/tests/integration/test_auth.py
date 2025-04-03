"""Tests for authentication middleware."""

import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Mock the google.cloud modules early
sys.modules["google.cloud"] = MagicMock()
sys.modules["google.cloud.secretmanager"] = MagicMock()
sys.modules["google.cloud.secretmanager_v1"] = MagicMock()

# Import after mocking
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.auth import TokenManager, security
from app.core.config import get_settings
from app.main import app


@pytest.fixture
def test_client():
    """Create a test client for the FastAPI app."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def test_client_with_rejection():
    """Create a test client with TokenManager modified to reject all tokens."""
    # Save the original method
    original_verify_token = TokenManager.verify_token

    # Replace with a mock that always returns False
    async def mock_verify_token(cls, token):
        return False

    # Apply the patch
    TokenManager.verify_token = classmethod(mock_verify_token)

    # Ensure testing mode is off to force auth checks
    original_testing = os.environ.get("TESTING")
    os.environ["TESTING"] = "false"

    # Create the client
    with TestClient(app) as client:
        yield client

    # Restore original method and settings
    TokenManager.verify_token = original_verify_token

    if original_testing:
        os.environ["TESTING"] = original_testing
    else:
        os.environ.pop("TESTING", None)


@pytest.fixture(autouse=True)
def auth_env():
    """Set up authentication environment for tests."""
    # Store original env vars
    orig_testing = os.environ.get("TESTING")
    orig_token = os.environ.get("API_TOKEN")

    # Set test environment
    os.environ["TESTING"] = "true"
    os.environ["API_TOKEN"] = "test-token"  # noqa: S105

    yield

    # Restore original env vars
    if orig_testing:
        os.environ["TESTING"] = orig_testing
    else:
        os.environ.pop("TESTING", None)

    if orig_token:
        os.environ["API_TOKEN"] = orig_token
    else:
        os.environ.pop("API_TOKEN", None)


def test_health_endpoint_no_auth(test_client):
    """Test that health endpoint is accessible without authentication."""
    response = test_client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_docs_endpoint_no_auth(test_client):
    """Test that documentation endpoints are accessible without authentication."""
    response = test_client.get("/api/docs")
    assert response.status_code == 200

    response = test_client.get("/api/redoc")
    assert response.status_code == 200

    response = test_client.get("/api/openapi.json")
    assert response.status_code == 200


def test_auth_required_endpoint_in_test_mode(test_client):
    """Test that auth-required endpoint works in test mode without token."""
    # In test mode, authentication should be bypassed
    response = test_client.get("/api/health/auth-test")
    assert response.status_code == 200
    assert response.json()["status"] == "authenticated"


def test_auth_required_endpoint_with_valid_token():
    """Test that auth-required endpoint works with valid token."""
    # Prepare a test client with testing mode off
    os.environ["TESTING"] = "false"
    try:
        with TestClient(app) as client:
            # Send request with valid token
            response = client.get(
                "/api/health/auth-test", headers={"Authorization": "Bearer test"}
            )
            assert response.status_code == 200
            assert response.json()["status"] == "authenticated"
    finally:
        # Restore testing mode
        os.environ["TESTING"] = "true"


def test_auth_required_endpoint_without_token():
    """Test that auth-required endpoint fails without token."""
    # Prepare a test client with testing mode off
    os.environ["TESTING"] = "false"
    try:
        with TestClient(app) as client:
            # Send request without token
            response = client.get("/api/health/auth-test")
            assert response.status_code == 401
            assert "Not authenticated" in response.json()["detail"]
    finally:
        # Restore testing mode
        os.environ["TESTING"] = "true"


def test_auth_required_endpoint_with_invalid_token(test_client_with_rejection):
    """Test that auth-required endpoint fails with invalid token."""
    # Test client with TokenManager modified to reject all tokens
    response = test_client_with_rejection.get(
        "/api/health/auth-test", headers={"Authorization": "Bearer any-token"}
    )
    assert response.status_code == 401
    assert "Invalid token" in response.json()["detail"]


def test_auth_required_endpoint_with_malformed_token():
    """Test that auth-required endpoint fails with malformed token."""
    # Prepare a test client with testing mode off
    os.environ["TESTING"] = "false"
    try:
        with TestClient(app) as client:
            # Send request with malformed token
            response = client.get(
                "/api/health/auth-test", headers={"Authorization": "NotBearer token"}
            )
            assert response.status_code == 401
            assert "Not authenticated" in response.json()["detail"]
    finally:
        # Restore testing mode
        os.environ["TESTING"] = "true"
