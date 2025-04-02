"""Router for document query operations.

This module provides endpoints for querying documents using vector similarity
search and generating responses with OpenAI's API.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from app.services.documents.query import process_query
from app.models.query import QueryRequest, QueryResponse

# Create router
router = APIRouter(tags=["query"])


@router.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest) -> QueryResponse:
    """Process a query against the document collection.

    Args:
        request: Query parameters including query text, max results and temperature

    Returns:
        QueryResponse containing the answer and sources

    Raises:
        HTTPException: If query processing fails
    """
    try:
        return await process_query(
            query=request.query,
            max_results=request.max_results,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to process query: {str(e)}"
        ) from e


@router.post("/rag-search", response_model=QueryResponse)
async def rag_search(request: QueryRequest) -> QueryResponse:
    """Process a RAG (Retrieval Augmented Generation) search request.

    This endpoint retrieves relevant document chunks and generates
    an AI response based on those chunks.

    Args:
        request: Query parameters including query text and generation settings

    Returns:
        QueryResponse containing the AI-generated answer, sources, and confidence

    Raises:
        HTTPException: If RAG processing fails
    """
    try:
        return await process_query(
            query=request.query,
            max_results=request.max_results,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to process RAG query: {str(e)}"
        ) from e
