"""Search router for document search and retrieval.

This module provides endpoints for searching documents using vector similarity.
"""

import logging
from typing import List, Dict, Any, Union
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.orm import Session

from app.services.documents.search import search_documents, legacy_search_documents
from app.models.search import (
    SearchQuery,
    SearchResult,
    QueryRequest,
    QueryResponse,
    LegalSearchRequest,
    LegalSearchResponse,
    SimpleDocumentResult,
)
from app.services.database.vector_service import vector_service
from app.services.database.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/", response_model=List[SearchResult])
async def search_documents_endpoint(request: SearchQuery):
    """Search for documents using vector similarity.

    Args:
        request: Search query parameters

    Returns:
        List of document chunks and metadata

    Raises:
        HTTPException: If search fails
    """
    try:
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        return await search_documents(request)
    except HTTPException:
        raise
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to search documents: {str(e)}"
        ) from e


@router.post("/api", response_model=QueryResponse)
async def legacy_search_endpoint(request: QueryRequest) -> QueryResponse:
    """Search for relevant document chunks using the old API format.

    This endpoint is preserved for backward compatibility.

    Args:
        request: Search parameters including query text and filters

    Returns:
        QueryResponse containing matched chunks and their metadata

    Raises:
        HTTPException: If search fails
    """
    try:
        if not request:
            raise HTTPException(status_code=400, detail="Missing request body")
        if not request.query_text.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        return await legacy_search_documents(request)
    except HTTPException:
        raise
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to search documents: {str(e)}"
        ) from e


@router.post("/legal", response_model=None)
async def legal_document_search(request: LegalSearchRequest, db: Session = None):
    """Search for legal documents using semantic vector similarity with context.

    This endpoint provides specialized search for legal documents with options
    for surrounding context chunks and document metadata.

    Args:
        request: Legal search parameters including query text and context options
        db: Database session

    Returns:
        Either a structured response with context chunks (when context_window > 0)
        or a simple list of results (when context_window = 0)

    Raises:
        HTTPException: If search fails
    """
    # Resolve the dependency here instead of in the parameter default
    if db is None:
        db = get_db()

    try:
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        # Prepare filters dictionary from request
        filters = {}
        if request.document_source:
            filters["document_source"] = request.document_source

        # Call the enhanced vector_search method
        try:
            results = await vector_service.vector_search(
                db=db,
                query_text=request.query,
                limit=request.top_k,
                min_score=request.min_relevance,
                filters=filters,
                include_document_metadata=request.include_document_metadata,
                context_window=request.context_window,
            )

            return results

        except Exception as e:
            logger.error(f"Vector search error: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Error performing vector search: {str(e)}"
            ) from e

    except HTTPException:
        raise
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.exception("Legal search error")
        raise HTTPException(
            status_code=500, detail=f"Failed to search legal documents: {str(e)}"
        ) from e
