"""FastAPI service for legal document RAG system.

This module provides REST API endpoints for Retool to interact with the
Chroma vector database.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, TypeVar, cast

import chromadb
import uvicorn
from chromadb.config import Settings
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Constants
EMBEDDING_MODEL = "text-embedding-3-small"  # Updated to latest model
CHROMA_PERSIST_DIR = Path("cache/chroma")
API_VERSION = "1.0.0"

# Type variables
T = TypeVar("T", bound=BaseModel)

# Initialize FastAPI app with metadata
app = FastAPI(
    title="Legal Document Search API",
    description="API for searching legal documents using semantic similarity",
    version=API_VERSION,
    docs_url="/",  # Swagger UI at root endpoint
)

# Add CORS middleware for Retool
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    # Initialize OpenAI embedding function
    openai_ef = OpenAIEmbeddingFunction(
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name=EMBEDDING_MODEL,
    )

    # Initialize Chroma client
    chroma_client = chromadb.PersistentClient(
        path=str(CHROMA_PERSIST_DIR),
        settings=Settings(
            anonymized_telemetry=False,
            allow_reset=True,
            is_persistent=True,
        ),
    )

    # Get or create collection
    collection = chroma_client.get_or_create_collection(
        name="legal_docs",
        embedding_function=openai_ef,
    )
    logger.info("Successfully initialized Chroma client and collection")

except Exception as e:
    logger.error(f"Failed to initialize Chroma: {str(e)}")
    raise


# Request/Response Models
class QueryRequest(BaseModel):
    """Request model for document search queries."""

    query_text: str = Field(..., min_length=1, description="The text to search for")
    n_results: int = Field(
        default=5, ge=1, le=20, description="Number of results to return"
    )
    min_similarity: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Minimum similarity threshold (0 to 1)",
    )
    metadata_filter: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional metadata filters",
    )


class SearchResult(BaseModel):
    """Model representing a single search result."""

    chunk: str = Field(..., description="The matched text chunk")
    metadata: Dict[str, Any] = Field(..., description="Document metadata")
    similarity: float = Field(..., description="Similarity score (0 to 1)")
    rank: int = Field(..., description="Result rank")


class QueryResponse(BaseModel):
    """Response model for search queries."""

    results: List[SearchResult] = Field(..., description="List of search results")
    total_found: int = Field(..., description="Total number of results")


def get_request() -> Request:
    """Get FastAPI request object.

    Returns:
        Request: The FastAPI request object
    """
    return Request(scope={"type": "http"})


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all unhandled exceptions globally.

    Args:
        request: The incoming request
        exc: The exception that was raised

    Returns:
        JSONResponse with error details
    """
    logger.error(f"Global error handler caught: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)},
    )


@app.post("/api/search", response_model=QueryResponse, tags=["Search"])
async def search_documents(request: QueryRequest = None) -> QueryResponse:
    """Search for relevant document chunks.

    This endpoint searches the document collection using semantic similarity and returns
    the most relevant chunks based on the query.

    Args:
        request: Search parameters including query text and filters

    Returns:
        QueryResponse containing matched chunks and their metadata

    Raises:
        HTTPException: If the search fails or no results are found
    """
    try:
        if not request:
            raise HTTPException(status_code=400, detail="Missing request body")

        logger.info(f"Processing search request: {request.query_text}")

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
        for idx, (doc, metadata, distance) in enumerate(
            zip(documents, metadatas, distances)
        ):
            # Convert distance to similarity score (0 to 1)
            similarity = 1 - (distance / 2)

            # Skip results below similarity threshold
            if similarity < request.min_similarity:
                continue

            formatted_results.append(
                SearchResult(
                    chunk=doc,
                    metadata=cast(Dict[str, Any], metadata),
                    similarity=similarity,
                    rank=idx + 1,
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
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/api/health", tags=["System"])
async def health_check() -> Dict[str, Any]:
    """Check the health status of the API and its dependencies.

    Returns:
        Dict containing API status and version information
    """
    try:
        # Test Chroma connection
        collection.count()
        return {
            "status": "healthy",
            "version": API_VERSION,
            "chroma_status": "connected",
            "document_count": collection.count(),
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {"status": "unhealthy", "version": API_VERSION, "error": str(e)}


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
