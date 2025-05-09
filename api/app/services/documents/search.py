"""Search service for document search and retrieval.

This module provides functionality for searching documents using vector similarity.
"""

from typing import Any, Dict, List, cast

from sqlalchemy.orm import Session
from fastapi import Depends

from app.core.struct_logger import log
from app.core.config import get_settings
from app.models.search import QueryRequest, QueryResponse, SearchQuery, SearchResult
from app.services.database.vector_service import vector_service
from app.services.database.database import get_db

settings = get_settings()


async def search_documents(request: SearchQuery) -> List[SearchResult]:
    """Search for documents using vector similarity.

    Args:
        request: Search query parameters

    Returns:
        List of document chunks and metadata
    """
    try:
        # Log the request
        log.info("Search query", query=request.query)

        # Create database session
        db = next(get_db())

        # Use vector_service for search
        results = await vector_service.vector_search(
            db=db,
            query_text=request.query,
            limit=request.limit,
            include_document_metadata=True,
        )

        # Format results
        search_results = []
        for result in results:
            # Field names need to match what's returned by vector_service
            content_field = "chunk_content" if "chunk_content" in result else "content"
            sequence_field = "chunk_sequence" if "chunk_sequence" in result else None

            search_results.append(
                SearchResult(
                    text=result[content_field],
                    metadata={
                        "document_id": result["document_id"],
                        "document_source": result.get("document_source"),
                        "document_file_path": result.get("document_file_path"),
                        "chunk_id": result["chunk_id"],
                        "chunk_sequence": result.get(sequence_field)
                        if sequence_field
                        else None,
                    },
                    distance=1.0
                    - result["similarity_score"],  # Convert similarity to distance
                )
            )

        return search_results

    except Exception as e:
        log.error("Error during search", error=str(e))
        raise


async def legacy_search_documents(request: QueryRequest) -> QueryResponse:
    """Search for relevant document chunks using the old API format.

    Args:
        request: Search parameters including query text and filters

    Returns:
        QueryResponse containing matched chunks and their metadata
    """
    try:
        if not request:
            raise ValueError("Missing request body")

        log.info("Processing search request", query=request.query_text)

        # Create database session
        db = next(get_db())

        # Prepare filters
        filters = {}
        if request.metadata_filter:
            for key, value in request.metadata_filter.items():
                # Map metadata filter to appropriate filters for vector_service
                if key.startswith("document_"):
                    filters[key] = value
                else:
                    # For chunk-level filters
                    filters[key] = value

        # Use vector_service for search
        results = await vector_service.vector_search(
            db=db,
            query_text=request.query_text,
            limit=request.n_results,
            min_score=request.min_similarity,
            filters=filters,
            include_document_metadata=True,
        )

        if not results:
            log.warning("No results found for query")
            return QueryResponse(results=[], total_found=0)

        # Process results
        formatted_results = []
        for result in results:
            # Field names need to match what's returned by vector_service
            content_field = "chunk_content" if "chunk_content" in result else "content"
            sequence_field = "chunk_sequence" if "chunk_sequence" in result else None

            formatted_results.append(
                SearchResult(
                    text=result[content_field],
                    metadata={
                        "document_id": result["document_id"],
                        "document_source": result.get("document_source"),
                        "document_file_path": result.get("document_file_path"),
                        "chunk_id": result["chunk_id"],
                        "chunk_sequence": result.get(sequence_field)
                        if sequence_field
                        else None,
                    },
                    distance=1.0
                    - result["similarity_score"],  # Convert similarity to distance
                )
            )

        log.info("Search results found", count=len(formatted_results))
        return QueryResponse(
            results=formatted_results,
            total_found=len(formatted_results),
        )

    except Exception as e:
        log.error("Search failed", error=str(e))
        raise
