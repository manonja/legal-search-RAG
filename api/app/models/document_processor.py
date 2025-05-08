"""Document processor models.

This module contains Pydantic models for document processing operations.
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field


class DocumentInput(BaseModel):
    """Model representing a document to be processed."""

    document_id: Optional[str] = Field(
        None, description="Document ID if already in datastore"
    )
    content: Optional[str] = Field(
        None, description="Document content if already extracted"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Document metadata"
    )


class DocumentChunk(BaseModel):
    """Model representing a processed document chunk."""

    text: str = Field(..., description="Chunk text content")
    metadata: Dict[str, Any] = Field(..., description="Chunk metadata")
    chunk_id: Optional[str] = Field(None, description="Generated chunk ID")
    token_count: Optional[int] = Field(None, description="Number of tokens in chunk")


class ProcessedDocument(BaseModel):
    """Model representing a fully processed document."""

    document_id: str = Field(..., description="Unique document ID")
    original_filename: str = Field(..., description="Original document filename")
    chunks: List[DocumentChunk] = Field(..., description="List of processed chunks")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Document metadata"
    )
    total_chunks: int = Field(..., description="Total number of chunks")
