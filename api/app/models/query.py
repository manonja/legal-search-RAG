"""Query models for document search operations.

This module defines the Pydantic models used for handling document query requests
and responses.
"""

from pydantic import BaseModel, Field
from typing import List, Optional


class QueryRequest(BaseModel):
    """Request model for document queries."""

    query: str = Field(..., min_length=1, description="The text to search for")
    max_results: Optional[int] = 5
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000


class SourceInfo(BaseModel):
    """Model representing information about a source document."""

    filename: str = Field(
        ..., description="The original filename of the source document"
    )
    document_id: str = Field(..., description="The unique ID (UUID) of the document")


class QueryResponse(BaseModel):
    """Response model for document queries."""

    answer: str = Field(..., description="The generated answer to the query")
    sources: List[SourceInfo] = Field(
        ..., description="List of source documents used for the answer"
    )
    confidence: float = Field(
        ..., description="Confidence score of the answer (0.0 to 1.0)"
    )
