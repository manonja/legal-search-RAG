"""Search service for document search and retrieval.

This module provides functionality for searching documents using vector similarity.
"""

from typing import Any, Dict, List, Optional, cast

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.api.types import IncludeEnum
from app.core.struct_logger import log

from app.core.config import get_settings
from app.models.search import QueryRequest, QueryResponse, SearchQuery, SearchResult
from app.services.database.chroma import get_collection


async def search_documents(
    request: SearchQuery, collection_name: Optional[str] = None
) -> List[SearchResult]:
    """Search for documents using vector similarity.

    Args:
        request: Search query parameters
        collection_name: Optional name of collection to search in

    Returns:
        List of document chunks and metadata
    """
    try:
        # Log the request
        log.info(
            "Search query", query=request.query, collection=collection_name or "default"
        )

        # Get collection
        collection = await get_collection(collection_name)

        # Check if collection exists
        if collection is None:
            log.error(
                "Failed to get Chroma collection - collection is None",
                collection_name=collection_name,
            )
            raise ValueError("Document collection not available")

        # Query the collection
        results = collection.query(
            query_texts=[request.query],
            n_results=request.limit,
            include=[
                IncludeEnum.documents,
                IncludeEnum.metadatas,
                IncludeEnum.distances,
            ],
        )

        # Format results
        search_results = []
        if (
            results["documents"] is None
            or results["metadatas"] is None
            or results["distances"] is None
        ):
            return []

        for i in range(len(results["documents"][0])):
            search_results.append(
                SearchResult(
                    text=results["documents"][0][i],
                    metadata=dict(results["metadatas"][0][i]),
                    distance=float(results["distances"][0][i]),
                )
            )

        return search_results

    except Exception as e:
        log.error("Error during search", error=str(e), collection=collection_name)
        raise


async def legacy_search_documents(
    request: QueryRequest, collection_name: Optional[str] = None
) -> QueryResponse:
    """Search for relevant document chunks using the old API format.

    Args:
        request: Search parameters including query text and filters
        collection_name: Optional name of collection to search in

    Returns:
        QueryResponse containing matched chunks and their metadata
    """
    try:
        if not request:
            raise ValueError("Missing request body")

        log.info(
            "Processing search request",
            query=request.query_text,
            collection=collection_name or "default",
        )

        # Get collection
        collection = await get_collection(collection_name)

        # Check if collection exists
        if collection is None:
            log.error(
                "Failed to get Chroma collection - collection is None",
                collection_name=collection_name,
            )
            raise ValueError("Document collection not available")

        # Query Chroma
        results = collection.query(
            query_texts=[request.query_text],
            n_results=request.n_results,
            where=request.metadata_filter,
            include=[
                IncludeEnum.documents,
                IncludeEnum.metadatas,
                IncludeEnum.distances,
            ],
        )

        if not results or not results.get("documents"):
            log.warning("No results found for query", collection=collection_name)
            return QueryResponse(results=[], total_found=0)

        if (
            results["documents"] is None
            or results["metadatas"] is None
            or results["distances"] is None
        ):
            return QueryResponse(results=[], total_found=0)

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        if not documents:
            log.warning("No documents found in results", collection=collection_name)
            return QueryResponse(results=[], total_found=0)

        # Process results
        formatted_results = []
        for _, (doc, metadata, distance) in enumerate(
            zip(documents, metadatas, distances, strict=False)
        ):
            # Convert distance to similarity score (0 to 1)
            similarity = 1 - (distance / 2)

            # Skip results below similarity threshold
            if similarity < request.min_similarity:
                continue

            formatted_results.append(
                SearchResult(
                    text=doc,
                    metadata=dict(metadata),
                    distance=distance,
                )
            )

        log.info(
            "Search results found",
            count=len(formatted_results),
            threshold="above similarity threshold",
            collection=collection_name,
        )
        return QueryResponse(
            results=formatted_results,
            total_found=len(formatted_results),
        )

    except Exception as e:
        log.error("Search failed", error=str(e), collection=collection_name)
        raise
