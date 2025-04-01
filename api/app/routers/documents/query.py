"""Router for document query operations.

This module provides endpoints for querying documents using vector similarity
search and generating responses with OpenAI's API.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from app.services.documents.query import process_query
from app.models.query import QueryRequest, QueryResponse

# Create router
router = APIRouter(prefix="/query", tags=["query"])


@router.post("/", response_model=QueryResponse)
async def query_documents(request: QueryRequest) -> QueryResponse:
    """Process a query against the document collection.

    Args:
        request: Query parameters including text and filters

    Returns:
        QueryResponse containing the answer and sources

    Raises:
        HTTPException: If query processing fails
    """
    try:
        return await process_query(
            query=request.query_text,
            max_results=request.n_results,
            temperature=0.7,  # Default temperature
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to process query: {str(e)}"
        ) from e
