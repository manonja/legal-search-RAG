"""Tests for document query service."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.documents.query import process_query, get_openai_client
from app.models.search import SearchResult
from app.models.query import SourceInfo
from tests.constants import TEST_QUERY
from app.core.config import get_settings

# Get settings
settings = get_settings()


@pytest.fixture
def mock_search_documents():
    """Mock the search_documents function."""
    with patch("app.services.documents.query.search_documents") as mock_search:
        mock_search.return_value = [
            SearchResult(
                text="Test document chunk 1",
                metadata={
                    "original_filename": "document1.pdf",
                    "document_id": "uuid-1",
                },
                distance=0.1,
            ),
            SearchResult(
                text="Test document chunk 2",
                metadata={
                    "original_filename": "document2.pdf",
                    "document_id": "uuid-2",
                },
                distance=0.3,
            ),
            SearchResult(
                text="Test document chunk 3 from doc 1",
                metadata={
                    "original_filename": "document1.pdf",
                    "document_id": "uuid-1",
                },
                distance=0.15,
            ),
        ]
        yield mock_search


@pytest.fixture
def mock_openai_response():
    """Mock the OpenAI client response."""

    class MockMessage:
        def __init__(self, content):
            self.content = content

    class MockChoice:
        def __init__(self, message):
            self.message = message

    class MockResponse:
        def __init__(self, choices):
            self.choices = choices

    message = MockMessage("This is a test AI response")
    return MockResponse([MockChoice(message)])


@pytest.fixture
def mock_openai_client(mock_openai_response):
    """Mock the OpenAI client."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_openai_response

    with patch("app.services.documents.query.get_openai_client") as get_client:
        get_client.return_value = mock_client
        yield mock_client


@pytest.mark.asyncio
async def test_process_query_success(mock_search_documents, mock_openai_client):
    """Test successful query processing."""
    result = await process_query(
        query=TEST_QUERY, max_results=5, temperature=0.7, max_tokens=1000
    )

    # Check result structure
    assert result.answer == "This is a test AI response"
    assert len(result.sources) == 2
    assert isinstance(result.sources[0], SourceInfo)
    assert isinstance(result.sources[1], SourceInfo)
    # Check content (order might vary, so check presence)
    source_docs = {(s.filename, s.document_id) for s in result.sources}
    assert ("document1.pdf", "uuid-1") in source_docs
    assert ("document2.pdf", "uuid-2") in source_docs

    # Check confidence calculation
    # (1.0 - (0.1 + 0.3 + 0.15)/3/2.0) = 1.0 - 0.55/3/2.0 = 1.0 - 0.0916... = 0.9083...
    # Original test used only first two, let's keep that for now, maybe adjust later
    # avg_distance = (0.1 + 0.3) / 2 -> confidence = 1.0 - 0.2 = 0.9
    # Update: Calculation now includes all results before deduplication for sources
    assert result.confidence == pytest.approx(1.0 - ((0.1 + 0.3 + 0.15) / 3 / 2.0))

    # Verify search was called with correct parameters
    mock_search_documents.assert_called_once()

    # Verify OpenAI was called with correct parameters
    mock_openai_client.chat.completions.create.assert_called_once()
    call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
    assert call_kwargs["temperature"] == 0.7
    assert call_kwargs["max_tokens"] == 1000
    assert call_kwargs["model"] == settings.OPENAI_MODEL


@pytest.mark.asyncio
async def test_process_query_no_results(mock_search_documents, mock_openai_client):
    """Test query processing with no search results."""
    # Setup mock to return empty results
    mock_search_documents.return_value = []

    result = await process_query(query=TEST_QUERY)

    # Check that we get a response indicating no information was found
    assert "I couldn't find any relevant information" in result.answer
    assert result.sources == []
    assert result.confidence == 0.0

    # Verify search was called but OpenAI was not called
    mock_search_documents.assert_called_once()
    mock_openai_client.chat.completions.create.assert_not_called()


@pytest.mark.asyncio
async def test_process_query_with_custom_params(
    mock_search_documents, mock_openai_client
):
    """Test query processing with custom parameters."""
    await process_query(
        query=TEST_QUERY,
        max_results=10,  # Custom value
        temperature=0.3,  # Custom value
        max_tokens=500,  # Custom value
    )

    # Verify search was called with the correct limit
    search_call_args = mock_search_documents.call_args[0][0]
    assert search_call_args.limit == 10

    # Verify OpenAI was called with the correct parameters
    openai_call_kwargs = mock_openai_client.chat.completions.create.call_args[1]
    assert openai_call_kwargs["temperature"] == 0.3
    assert openai_call_kwargs["max_tokens"] == 500


@pytest.mark.asyncio
async def test_process_query_search_error(mock_search_documents, mock_openai_client):
    """Test query processing with a search error."""
    # Setup mock to raise an exception
    mock_search_documents.side_effect = Exception("Search error")

    with pytest.raises(Exception) as exc_info:
        await process_query(query=TEST_QUERY)

    assert "Search error" in str(exc_info.value)
    mock_openai_client.chat.completions.create.assert_not_called()


@pytest.mark.asyncio
async def test_process_query_openai_error(mock_search_documents, mock_openai_client):
    """Test query processing with an OpenAI API error."""
    # Setup mock to raise an exception
    mock_openai_client.chat.completions.create.side_effect = Exception("OpenAI error")

    with pytest.raises(Exception) as exc_info:
        await process_query(query=TEST_QUERY)

    assert "OpenAI error" in str(exc_info.value)
    mock_search_documents.assert_called_once()


def test_get_openai_client():
    """Test that get_openai_client returns an OpenAI client."""
    with patch("app.services.documents.query.openai") as mock_openai:
        client = get_openai_client()

        # Verify OpenAI client was initialized with the API key from settings
        mock_openai.OpenAI.assert_called_once_with(api_key=settings.OPENAI_API_KEY)
        assert client == mock_openai.OpenAI.return_value
