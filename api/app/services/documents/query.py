"""Query service for document search and retrieval.

This module provides functionality to query documents using vector similarity search
and generate responses using OpenAI's API.
"""

from typing import Optional
import os

import openai
from app.core.struct_logger import log

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

        # Format context from search results with proper source and page info
        context_parts = []
        for result in search_results:
            # Prioritize the direct original_filename metadata key
            clean_source_name = result.metadata.get("original_filename")

            # If clean name isn't directly available, fallback to path cleaning
            if not clean_source_name:
                source_path = result.metadata.get(
                    "original_source"
                ) or result.metadata.get("source")
                if source_path:
                    base_name = os.path.basename(source_path)
                    if base_name.startswith("chunked_"):
                        clean_source_name = base_name[len("chunked_") :]
                    else:
                        clean_source_name = base_name
                    if clean_source_name.endswith(".txt"):
                        clean_source_name = clean_source_name[:-4]
                # Keep clean_source_name as None if no path found

            # Page number handling (remains the same)
            page_number_val = result.metadata.get("page_number")
            page_info = (
                f"Page: {page_number_val}" if page_number_val is not None else ""
            )

            # Format context part using the determined clean source name
            context_parts.append(
                f"Source Document: {clean_source_name}\n{page_info}\nExcerpt:\n{result.text}".strip()
            )
        # Use '---' as a clear separator between excerpts
        context = "\n---\n".join(context_parts)

        # Log the retrieved context for debugging
        log.debug("Context retrieved for LLM", context=context)

        # Create sources list for response using ORIGINAL filenames
        sources = []
        seen_sources = set()  # Use a set for efficient tracking of unique sources
        for result in search_results:
            # Prioritize the direct original_filename metadata key
            clean_source_name = result.metadata.get("original_filename")

            # If clean name isn't directly available, fallback to path cleaning
            if not clean_source_name:
                source_path = result.metadata.get(
                    "original_source"
                ) or result.metadata.get("source")
                if source_path:
                    base_name = os.path.basename(source_path)
                    if base_name.startswith("chunked_"):
                        clean_source_name = base_name[len("chunked_") :]
                    else:
                        clean_source_name = base_name
                    if clean_source_name.endswith(".txt"):
                        clean_source_name = clean_source_name[:-4]
                # Keep clean_source_name as None if no path found

            # Add the cleaned/retrieved name if it's valid and hasn't been seen
            if (
                clean_source_name
                and clean_source_name.strip()
                and clean_source_name not in seen_sources
            ):
                sources.append(clean_source_name.strip())
                seen_sources.add(clean_source_name.strip())

        # Generate prompt for OpenAI - Enhanced for clarity and citation
        system_message = "You are a highly proficient legal assistant AI specializing in analyzing provided legal document excerpts and providing accurate, cited answers."

        # Define the main prompt using a standard f-string for clarity
        prompt = f"""
        You are a highly proficient legal assistant AI. Your task is to answer the user's question based *solely* on the provided document excerpts.

        Follow these instructions precisely:
        1.  Analyze the user's QUESTION carefully.
        2.  Review the DOCUMENT EXCERPTS provided below. Each excerpt is clearly marked with its 'Source Document' and potentially a 'Page'.
        3.  Synthesize a comprehensive and accurate answer to the QUESTION using *only* information found in the excerpts.
        4.  Structure your answer clearly. Use headings, lists, or paragraphs as appropriate for readability.
        5.  **Crucially, whenever you state a fact or principle derived from an excerpt, you MUST cite the source. Use the format (Source Document: [Document Name], Page: [Page Number]) if the page number is provided for that excerpt. If the page number is NOT provided for an excerpt, use the format (Source Document: [Document Name]).** Do not invent citations or cite generally. Use the exact 'Source Document' and 'Page' values provided.
        6.  If the excerpts do not contain the information needed to answer the question, state clearly: "Based on the provided documents, I cannot answer this question." Do not use external knowledge.
        7.  Keep the tone professional and objective.

        DOCUMENT EXCERPTS:
        ---
        {context}
        ---

        QUESTION: {query}

        Answer:
        """

        # Get OpenAI client
        client = get_openai_client()

        # Call OpenAI API for response generation
        log.info("Generating response with OpenAI", model=settings.OPENAI_MODEL)
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,  # Ensure this uses a capable model like gpt-4-turbo
            messages=[
                {
                    "role": "system",
                    "content": system_message,  # Use updated system message
                },
                {"role": "user", "content": prompt},  # Use updated prompt
            ],
            # Consider lower temp (e.g., 0.2) for more factual/cited answers
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
