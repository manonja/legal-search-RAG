"""Tests for the custom HuggingFace embedding function."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.database.embedding_function import HuggingFaceEmbeddingFunction


@pytest.fixture
def mock_embedding_client():
    """Create a mock embedding client with async create_embeddings method."""
    client = MagicMock()
    client.model_name = "nlpaueb/legal-bert-base-uncased"
    client.create_embeddings = AsyncMock()
    # Sample response - 768-dimensional vectors (legal-bert-base-uncased)
    client.create_embeddings.return_value = [
        [0.1] * 768,  # First embedding
        [0.2] * 768,  # Second embedding
    ]
    return client


def test_huggingface_embedding_function_init(mock_embedding_client):
    """Test initialization of the embedding function."""
    # Initialize the embedding function with the mock client directly
    ef = HuggingFaceEmbeddingFunction(client=mock_embedding_client)

    # Check that the client was set correctly
    assert ef.client == mock_embedding_client
    assert ef.batch_size == 32  # Default batch size


@patch("app.services.database.embedding_function._get_embedding_client")
def test_huggingface_embedding_function_init_default(
    mock_get_client, mock_embedding_client
):
    """Test initialization of the embedding function with the default client getter."""
    mock_get_client.return_value = mock_embedding_client

    # Initialize the embedding function without providing a client
    ef = HuggingFaceEmbeddingFunction()

    # Check that the client was retrieved
    mock_get_client.assert_called_once()
    assert ef.client == mock_embedding_client
    assert ef.batch_size == 32  # Default batch size


def test_huggingface_embedding_function_call(mock_embedding_client):
    """Test calling the embedding function."""
    # Initialize the embedding function with the mock client
    ef = HuggingFaceEmbeddingFunction(batch_size=2, client=mock_embedding_client)

    # Call the embedding function
    texts = ["This is a test", "This is another test"]
    embeddings = ef(texts)

    # Check the results
    assert len(embeddings) == 2
    assert len(embeddings[0]) == 768  # legal-bert-base-uncased dimension
    assert mock_embedding_client.create_embeddings.called
    # Should be called with the texts
    mock_embedding_client.create_embeddings.assert_called_once_with(texts)


def test_huggingface_embedding_function_batching(mock_embedding_client):
    """Test batching in the embedding function."""
    # Set up the mock to return different results for different batches
    mock_embedding_client.create_embeddings.side_effect = [
        [[0.1] * 768, [0.2] * 768],  # First batch
        [[0.3] * 768, [0.4] * 768],  # Second batch
        [[0.5] * 768],  # Third batch (partial)
    ]

    # Initialize the embedding function with batch size 2
    ef = HuggingFaceEmbeddingFunction(batch_size=2, client=mock_embedding_client)

    # Call the embedding function with 5 texts
    texts = ["Text 1", "Text 2", "Text 3", "Text 4", "Text 5"]
    embeddings = ef(texts)

    # Check batching behavior
    assert len(embeddings) == 5
    assert mock_embedding_client.create_embeddings.call_count == 3

    # First batch should have texts 0-1
    assert mock_embedding_client.create_embeddings.call_args_list[0][0][0] == texts[0:2]
    # Second batch should have texts 2-3
    assert mock_embedding_client.create_embeddings.call_args_list[1][0][0] == texts[2:4]
    # Third batch should have text 4
    assert mock_embedding_client.create_embeddings.call_args_list[2][0][0] == texts[4:5]


@patch("chromadb.api.types.validate_embeddings")
@patch("chromadb.api.types.normalize_embeddings")
def test_huggingface_embedding_function_empty_input(
    mock_normalize, mock_validate, mock_embedding_client
):
    """Test calling the embedding function with empty input."""
    # Set up mocks to allow empty list
    mock_normalize.return_value = []
    mock_validate.return_value = []

    # Initialize the embedding function
    ef = HuggingFaceEmbeddingFunction(client=mock_embedding_client)

    # Call the embedding function with empty input
    embeddings = ef([])

    # Check that no embeddings were generated and create_embeddings was not called
    assert embeddings == []
    assert not mock_embedding_client.create_embeddings.called
