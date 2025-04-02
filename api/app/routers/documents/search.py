"""Search router for document search and retrieval.

This module provides endpoints for searching documents using vector similarity.
"""

from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, ValidationError

from app.services.documents.search import search_documents, legacy_search_documents
from app.models.search import SearchQuery, SearchResult, QueryRequest, QueryResponse

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
