"""Search service for document search and retrieval.

This module provides functionality for searching documents using vector similarity.
"""

import logging
from typing import List, Dict, Any

from app.core.config import get_settings
from app.models.search import SearchQuery, SearchResult, QueryRequest, QueryResponse
from app.utils.chroma import get_collection

logger = logging.getLogger(__name__)


async def search_documents(request: SearchQuery) -> List[SearchResult]:
    """Search for documents using vector similarity.

    Args:
        request: Search query parameters

    Returns:
        List of document chunks and metadata
    """
    try:
        # Log the request
        logger.info(f"Search query: {request.query}")

        # Get collection
        collection = await get_collection()

        # Query the collection
        results = collection.query(
            query_texts=[request.query],
            n_results=request.limit,
            include=["documents", "metadatas", "distances"],
        )

        # Format results
        search_results = []
        for i in range(len(results["documents"][0])):
            search_results.append(
                SearchResult(
                    text=results["documents"][0][i],
                    metadata=results["metadatas"][0][i],
                    distance=float(results["distances"][0][i]),
                )
            )

        return search_results

    except Exception as e:
        logger.error(f"Error during search: {e}")
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

        logger.info(f"Processing search request: {request.query_text}")

        # Get collection
        collection = await get_collection()

        # Query Chroma
        results = collection.query(
            query_texts=[request.query_text],
            n_results=request.n_results,
            where=request.metadata_filter,
            include=["documents", "metadatas", "distances"],
        )

        if not results or not results.get("documents"):
            logger.warning("No results found for query")
            return QueryResponse(results=[], total_found=0)

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        if not documents:
            logger.warning("No documents found in results")
            return QueryResponse(results=[], total_found=0)

        # Process results
        formatted_results = []
        for _, (doc, metadata, distance) in enumerate(
            zip(documents, metadatas, distances)
        ):
            # Convert distance to similarity score (0 to 1)
            similarity = 1 - (distance / 2)

            # Skip results below similarity threshold
            if similarity < request.min_similarity:
                continue

            formatted_results.append(
                SearchResult(
                    text=doc,
                    metadata=metadata,
                    distance=distance,
                )
            )

        logger.info(
            f"Found {len(formatted_results)} results above similarity threshold"
        )
        return QueryResponse(
            results=formatted_results,
            total_found=len(formatted_results),
        )

    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise
