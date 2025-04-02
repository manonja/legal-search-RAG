"""Authentication-specific fixtures for testing.

This module provides fixtures for testing authentication without
requiring real Secret Manager access.
"""

import os
import sys
import pytest
from unittest.mock import MagicMock

# Mock Google Cloud modules for testing
if "google.cloud.secretmanager" not in sys.modules:
    sys.modules["google.cloud"] = MagicMock()
    sys.modules["google.cloud.secretmanager"] = MagicMock()
    sys.modules["google.cloud.secretmanager_v1"] = MagicMock()


@pytest.fixture(autouse=True)
def testing_env():
    """Set TESTING environment variable."""
    # Store original value
    original_testing = os.environ.get("TESTING")

    # Set testing mode
    os.environ["TESTING"] = "true"

    yield

    # Restore original value
    if original_testing:
        os.environ["TESTING"] = original_testing
    else:
        os.environ.pop("TESTING", None)


@pytest.fixture
def mock_api_token():
    """Set API token for testing."""
    # Store original value
    original_token = os.environ.get("API_TOKEN")

    # Set test token
    test_token = "test-auth-token-12345"  # noqa: S105
    os.environ["API_TOKEN"] = test_token

    yield test_token

    # Restore original value
    if original_token:
        os.environ["API_TOKEN"] = original_token
    else:
        os.environ.pop("API_TOKEN", None)
