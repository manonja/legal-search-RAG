"""Query models for document search operations.

This module defines the Pydantic models used for handling document query requests
and responses.
"""

from pydantic import BaseModel
from typing import List, Optional


class QueryRequest(BaseModel):
    """Request model for document queries."""

    query: str
    max_results: Optional[int] = 5
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1000


class QueryResponse(BaseModel):
    """Response model for document queries."""

    answer: str
    sources: List[str]
    confidence: float
