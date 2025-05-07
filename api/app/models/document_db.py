"""Document database models.

This module contains Pydantic models for document database operations.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class DocumentChunkBase(BaseModel):
    """Base model for document chunks."""

    chunk_index: int = Field(..., description="Index of the chunk within the document")
    content: str = Field(..., description="Content of the document chunk")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Chunk metadata")


class DocumentChunkCreate(DocumentChunkBase):
    """Model for creating document chunks."""

    pass


class DocumentChunkDB(DocumentChunkBase):
    """Model for document chunks from the database."""

    id: int = Field(..., description="Unique identifier for the document chunk")
    document_id: int = Field(..., description="ID of the parent document")
    created_at: datetime = Field(..., description="Creation timestamp")

    model_config = ConfigDict(from_attributes=True)


class DocumentBase(BaseModel):
    """Base model for documents."""

    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Full document content")
    source: str = Field(..., description="Document source identifier")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Document metadata")
    file_path: Optional[str] = Field(None, description="Path to the document file")


class DocumentCreate(DocumentBase):
    """Model for creating documents."""

    chunks: Optional[List[DocumentChunkCreate]] = Field(
        None, description="Document chunks"
    )


class DocumentUpdate(BaseModel):
    """Model for updating documents."""

    title: Optional[str] = Field(None, description="Document title")
    content: Optional[str] = Field(None, description="Full document content")
    source: Optional[str] = Field(None, description="Document source identifier")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Document metadata")
    file_path: Optional[str] = Field(None, description="Path to the document file")


class DocumentDB(DocumentBase):
    """Model for documents from the database."""

    id: int = Field(..., description="Unique identifier for the document")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    chunks: List[DocumentChunkDB] = Field(
        default_factory=list, description="Document chunks"
    )

    model_config = ConfigDict(from_attributes=True)


class VectorSearchQuery(BaseModel):
    """Model for vector search queries."""

    query: str = Field(..., description="Search query text")
    limit: int = Field(5, description="Number of results to return")
    min_score: Optional[float] = Field(None, description="Minimum similarity score")
