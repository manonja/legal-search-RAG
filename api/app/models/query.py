"""Query models for document search operations.

This module defines the Pydantic models used for handling document query requests
and responses.
"""

from pydantic import BaseModel
from typing import List, Optional


class QueryRequest(BaseModel):
    """Request model for document queries."""

    query: str
    top_k: Optional[int] = 5
    include_metadata: Optional[bool] = True


class QueryResponse(BaseModel):
    """Response model for document queries."""

    results: List[dict]
    query: str
    total_results: int
