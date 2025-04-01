"""Search models for document search and retrieval.

This module contains Pydantic models for search requests and responses.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class SearchQuery(BaseModel):
    """Search query parameters for basic vector search."""

    query: str = Field(..., description="Search query text")
    limit: int = Field(5, description="Maximum number of results to return")


class SearchResult(BaseModel):
    """Search result model."""

    text: str = Field(..., description="Document chunk text")
    metadata: Dict[str, Any] = Field(..., description="Document metadata")
    distance: float = Field(..., description="Similarity distance")


class QueryRequest(BaseModel):
    """Request model for document search queries (backward compatibility)."""

    query_text: str = Field(..., min_length=1, description="The text to search for")
    n_results: int = Field(
        default=3, ge=1, le=20, description="Number of results to return"
    )
    min_similarity: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum similarity threshold (0 to 1)",
    )
    metadata_filter: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional metadata filters",
    )


class QueryResponse(BaseModel):
    """Response model for search queries (backward compatibility)."""

    results: List[SearchResult] = Field(..., description="List of search results")
    total_found: int = Field(..., description="Total number of results")
