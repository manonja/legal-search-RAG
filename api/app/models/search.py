"""Search models for document search and retrieval.

This module contains Pydantic models for search requests and responses.
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class SearchQuery(BaseModel):
    """Search query parameters for basic vector search."""

    query: str = Field(..., min_length=1, description="Search query text")
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


# New models for legal document search


class ContextChunk(BaseModel):
    """Model for a context chunk from a document."""

    id: int = Field(..., description="Chunk ID")
    content: str = Field(..., description="Chunk content text")
    sequence: int = Field(..., description="Sequence number in document")


class DocumentMetadata(BaseModel):
    """Model for document metadata."""

    id: int = Field(..., description="Document ID")
    source: str = Field(..., description="Document source")
    file_path: Optional[str] = Field(None, description="Document file path")


class ChunkInfo(BaseModel):
    """Model for chunk information."""

    id: int = Field(..., description="Chunk ID")
    content: str = Field(..., description="Chunk content text")
    sequence: int = Field(..., description="Sequence number in document")


class LegalSearchResult(BaseModel):
    """Model for a legal document search result with context."""

    chunk: ChunkInfo = Field(..., description="Main chunk that matched the query")
    document: DocumentMetadata = Field(..., description="Document metadata")
    similarity_score: float = Field(..., description="Similarity score (0.0 to 1.0)")
    context_chunks: List[ContextChunk] = Field(
        default_factory=list, description="Surrounding chunks for context"
    )


class LegalSearchRequest(BaseModel):
    """Request model for legal document search."""

    query: str = Field(..., min_length=1, description="Legal query or question text")
    top_k: int = Field(
        default=5, ge=1, le=20, description="Number of top results to return"
    )
    min_relevance: float = Field(
        default=0.65, ge=0.0, le=1.0, description="Minimum relevance threshold (0 to 1)"
    )
    document_source: Optional[str] = Field(
        default=None, description="Optional filter for document source"
    )
    context_window: int = Field(
        default=1,
        ge=0,
        le=5,
        description="Number of surrounding chunks to include for context",
    )
    include_document_metadata: bool = Field(
        default=True, description="Whether to include document metadata"
    )


class LegalSearchResponse(BaseModel):
    """Response model for legal document search."""

    query: str = Field(..., description="Original query text")
    total_results: int = Field(..., description="Total number of results")
    results: List[Dict[str, Any]] = Field(
        ..., description="Search results with context"
    )


class SimpleDocumentResult(BaseModel):
    """Simple document result model without context."""

    chunk_id: int = Field(..., description="Chunk ID")
    document_id: int = Field(..., description="Document ID")
    content: str = Field(..., description="Chunk content")
    similarity_score: float = Field(..., description="Similarity score")
    document_source: Optional[str] = Field(None, description="Document source")
    document_file_path: Optional[str] = Field(None, description="Document file path")
    chunk_sequence: Optional[int] = Field(None, description="Chunk sequence number")
