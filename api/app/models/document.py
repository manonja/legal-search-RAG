"""Document models.

This module contains Pydantic models for document-related operations.
"""

from typing import Dict, List, Any
from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    """Response model for full document retrieval."""

    content: str = Field(..., description="Full document content")
    metadata: Dict[str, Any] = Field(..., description="Document metadata")
    source: str = Field(..., description="Document source path")
    chunks: List[str] = Field(..., description="List of chunks from this document")
