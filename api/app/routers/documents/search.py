"""Search router for document search and retrieval.

This module provides endpoints for searching documents using vector similarity.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks, Query
from pydantic import BaseModel, Field, ValidationError
import asyncio

from app.services.documents.search import search_documents, legacy_search_documents
from app.models.search import SearchQuery, SearchResult, QueryRequest, QueryResponse
from app.core.struct_logger import log

# Create router with correct prefix - no trailing slash
router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=List[SearchResult])
async def search_documents_endpoint(
    request: SearchQuery,
    background_tasks: BackgroundTasks,
    req: Request,
    collection_name: Optional[str] = Query(
        None, description="Optional custom collection name to search in"
    ),
):
    """Search for documents using vector similarity.

    Args:
        request: Search query parameters
        background_tasks: FastAPI background tasks
        req: FastAPI request object
        collection_name: Optional custom collection name to search in

    Returns:
        List of document chunks and metadata

    Raises:
        HTTPException: If search fails
    """
    # Log request for debugging
    log.info(
        "Search request received",
        query=request.query,
        limit=request.limit,
        collection=collection_name or "default",
        client_host=req.client.host if req.client else "unknown",
    )

    try:
        if not request.query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        # Increase timeout for this request
        # This is a workaround for the 307 redirect issue
        # The server is configured with timeout_keep_alive=30 in main.py
        results = await search_documents(request, collection_name)

        # Log success for debugging
        log.info(
            "Search completed successfully",
            query=request.query,
            num_results=len(results),
            collection=collection_name or "default",
        )

        return results
    except HTTPException:
        raise
    except ValidationError as e:
        log.error(
            "Validation error during search",
            error=str(e),
            query=request.query,
            collection=collection_name,
        )
        raise HTTPException(status_code=400, detail=str(e)) from e
    except asyncio.TimeoutError as e:
        log.error(
            "Search request timed out",
            error=str(e),
            query=request.query,
            collection=collection_name,
        )
        raise HTTPException(
            status_code=504,
            detail="Search request timed out. The RunPod inference is taking too long.",
        ) from e
    except Exception as e:
        log.error(
            "Error during search request",
            error=str(e),
            query=request.query,
            collection=collection_name,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to search documents: {str(e)}"
        ) from e


@router.post("/api", response_model=QueryResponse)
async def legacy_search_endpoint(
    request: QueryRequest,
    collection_name: Optional[str] = Query(
        None, description="Optional custom collection name to search in"
    ),
) -> QueryResponse:
    """Search for relevant document chunks using the old API format.

    This endpoint is preserved for backward compatibility.

    Args:
        request: Search parameters including query text and filters
        collection_name: Optional custom collection name to search in

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
        return await legacy_search_documents(request, collection_name)
    except HTTPException:
        raise
    except ValidationError as e:
        log.error(
            "Validation error during legacy search",
            error=str(e),
            collection=collection_name,
        )
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        log.error(
            "Error during legacy search", error=str(e), collection=collection_name
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to search documents: {str(e)}"
        ) from e
