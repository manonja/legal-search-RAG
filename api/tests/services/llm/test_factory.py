"""Tests for the LLM factory."""

import pytest
from unittest.mock import patch, MagicMock

from app.services.llm.factory import get_llm_client
from app.services.llm.runpod_client import RunPodClient


@patch("app.services.llm.factory.settings")
def test_get_llm_client_with_valid_configuration(mock_settings):
    """Test that get_llm_client returns a RunPodClient with valid configuration."""
    # Set up mock settings
    mock_settings.RUNPOD_API_KEY = "test_api_key"
    mock_settings.RUNPOD_MIXTRAL_ENDPOINT_ID = "test_endpoint_id"
    mock_settings.RUNPOD_MODEL_NAME = "mistralai/Mixtral-8x7B-v0.1"

    # Get client from factory
    client = get_llm_client()

    # Check that the client is a RunPodClient
    assert isinstance(client, RunPodClient)
    assert client.api_key == "test_api_key"
    assert client.endpoint_id == "test_endpoint_id"
    assert client.model_name == "mistralai/Mixtral-8x7B-v0.1"


@patch("app.services.llm.factory.settings")
def test_get_llm_client_missing_api_key(mock_settings):
    """Test that get_llm_client raises ValueError when API key is missing."""
    # Set up mock settings with missing API key
    mock_settings.RUNPOD_API_KEY = None
    mock_settings.RUNPOD_MIXTRAL_ENDPOINT_ID = "test_endpoint_id"

    # Check that the factory raises ValueError
    with pytest.raises(ValueError) as exc_info:
        get_llm_client()

    # Check error message
    assert "RUNPOD_API_KEY" in str(exc_info.value)
    assert "privacy-focused deployment" in str(exc_info.value)


@patch("app.services.llm.factory.settings")
def test_get_llm_client_missing_endpoint_id(mock_settings):
    """Test that get_llm_client raises ValueError when endpoint ID is missing."""
    # Set up mock settings with missing endpoint ID
    mock_settings.RUNPOD_API_KEY = "test_api_key"
    mock_settings.RUNPOD_MIXTRAL_ENDPOINT_ID = None

    # Check that the factory raises ValueError
    with pytest.raises(ValueError) as exc_info:
        get_llm_client()

    # Check error message
    assert "RUNPOD_MIXTRAL_ENDPOINT_ID" in str(exc_info.value)
    assert "privacy-focused deployment" in str(exc_info.value)


@patch(
    "app.services.llm.factory.getattr",
    side_effect=lambda obj, name, default: default
    if name == "RUNPOD_MODEL_NAME"
    else getattr(obj, name, default),
)
@patch("app.services.llm.factory.RunPodClient")
@patch("app.services.llm.factory.settings")
def test_get_llm_client_default_model_name(
    mock_settings, mock_runpod_client, mock_getattr
):
    """Test that get_llm_client uses default model name when not specified."""
    # Set up mock settings with required values
    mock_settings.RUNPOD_API_KEY = "test_api_key"
    mock_settings.RUNPOD_MIXTRAL_ENDPOINT_ID = "test_endpoint_id"
    # Note: Intentionally not setting RUNPOD_MODEL_NAME

    # Create mock client
    mock_client = MagicMock()
    mock_runpod_client.return_value = mock_client

    # Call the factory function
    client = get_llm_client()

    # Verify client was created with correct parameters
    mock_runpod_client.assert_called_once()
    call_args = mock_runpod_client.call_args
    assert call_args.kwargs["api_key"] == "test_api_key"
    assert call_args.kwargs["endpoint_id"] == "test_endpoint_id"
    assert call_args.kwargs["model_name"] == "mistralai/Mixtral-8x7B-v0.1"
