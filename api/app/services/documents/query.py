"""Query service for document search and retrieval.

This module provides functionality to query documents using vector similarity search
and generate responses using OpenAI's API.
"""

from typing import Optional

import openai
from struct_logger import log

from app.core.config import get_settings
from app.models.query import QueryResponse
from app.models.search import SearchQuery
from app.services.documents.search import search_documents


def get_openai_client():
    """Create and return an OpenAI client with the API key from settings."""
    settings = get_settings()
    return openai.OpenAI(api_key=settings.OPENAI_API_KEY)


async def process_query(
    query: str,
    max_results: Optional[int] = 5,
    temperature: Optional[float] = 0.7,
    max_tokens: Optional[int] = 1000,
) -> QueryResponse:
    """Process a query and generate a response using RAG.

    Args:
        query: The query text
        max_results: Maximum number of results to return
        temperature: Temperature for response generation
        max_tokens: Maximum tokens in the response

    Returns:
        QueryResponse containing the answer, sources, and confidence
    """
    settings = get_settings()
    log.info("Processing query", query=query)

    try:
        # First, search for relevant documents
        search_limit = (
            max_results if max_results is not None else 5
        )  # Use default if None
        search_results = await search_documents(
            SearchQuery(query=query, limit=search_limit)
        )

        if not search_results:
            log.warning("No search results found for query")
            return QueryResponse(
                answer="I couldn't find any relevant information to answer your question.",
                sources=[],
                confidence=0.0,
            )

        # Format context from search results
        context = "\n\n".join(
            [
                f"Document: {result.metadata.get('source', 'Unknown')}\n{result.text}"
                for result in search_results
            ]
        )

        # Create sources list for response
        sources = []
        for result in search_results:
            source = result.metadata.get("source", "Unknown")
            if source not in sources:
                sources.append(source)

        # Generate prompt for OpenAI
        prompt = f"""You are a legal assistant answering questions based on the provided document excerpts.
Answer the following question using ONLY the information from the provided document excerpts.
If the information needed is not present in the excerpts, say "I don't have enough information to answer this question."
Do not make up information or use your general knowledge.

DOCUMENT EXCERPTS:
{context}

QUESTION: {query}

Answer concisely and accurately, citing the relevant document sources when possible.
"""

        # Get OpenAI client
        client = get_openai_client()

        # Call OpenAI API for response generation
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "You are a legal assistant that answers questions based on provided documents.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Extract answer, handling potential None
        raw_answer = response.choices[0].message.content
        answer = raw_answer.strip() if raw_answer else ""

        # Calculate confidence based on similarity scores
        # Higher similarity (lower distance) = higher confidence
        avg_distance = sum(result.distance for result in search_results) / len(
            search_results
        )
        # Convert to confidence (1.0 - normalized distance)
        confidence = max(0.0, min(1.0, 1.0 - (avg_distance / 2.0)))

        log.info("Query processed successfully", confidence=round(confidence, 2))

        return QueryResponse(
            answer=answer,
            sources=sources,
            confidence=confidence,
        )

    except Exception as e:
        log.error("Error processing query", error=str(e))
        raise
