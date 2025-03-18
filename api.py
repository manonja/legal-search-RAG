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
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from utils.env import get_docs_root

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Constants
EMBEDDING_MODEL = "text-embedding-ada-002"  # Updated to latest model
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
    allow_origins=[
        "https://*.retool.com",  # Retool cloud domains
        "http://localhost:8000",  # Local development
        "http://localhost:3000",  # Next.js local development
        "https://*.ngrok.io",  # ngrok tunnels
        "https://*.ngrok-free.app",  # ngrok free tier domains
        "https://your-nextjs-domain.com",  # Production Next.js domain
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=86400,  # Cache preflight requests for 24 hours
)

try:
    # Initialize OpenAI embedding function
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
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

# Initialize OpenAI client
client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    timeout=60.0,  # Increase timeout for longer responses
)


# Request/Response Models
class QueryRequest(BaseModel):
    """Request model for document search queries."""

    query_text: str = Field(..., min_length=1, description="The text to search for")
    n_results: int = Field(
        default=5, ge=1, le=20, description="Number of results to return"
    )
    min_similarity: float = Field(
        default=0.8,
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


class RagResponse(BaseModel):
    """Response model for RAG-enhanced search queries."""

    context: List[SearchResult] = Field(..., description="Retrieved context documents")
    answer: str = Field(..., description="GPT-4 generated answer")
    total_found: int = Field(..., description="Total number of context documents found")


class DocumentResponse(BaseModel):
    """Response model for full document retrieval."""

    content: str = Field(..., description="Full document content")
    metadata: Dict[str, Any] = Field(..., description="Document metadata")
    source: str = Field(..., description="Document source path")
    chunks: List[str] = Field(..., description="List of chunks from this document")


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


@app.post("/api/rag-search", response_model=RagResponse, tags=["Search"])
async def rag_search(request: QueryRequest) -> RagResponse:
    """Search documents and generate answer using GPT-4.

    This endpoint combines vector search with GPT-4 processing to provide
    context-aware answers to legal questions.

    Args:
        request: Search parameters including query text and filters

    Returns:
        RagResponse containing context documents and GPT-4 generated answer

    Raises:
        HTTPException: If the search or GPT-4 processing fails
    """
    try:
        if not request:
            raise HTTPException(status_code=400, detail="Missing request body")

        logger.info(f"Processing RAG search request: {request.query_text}")

        # Query Chroma
        results = collection.query(
            query_texts=[request.query_text],
            n_results=request.n_results,
            where=request.metadata_filter,
            include=["documents", "metadatas", "distances"],
        )

        if not results or not results.get("documents"):
            logger.warning("No results found for query")
            return RagResponse(
                context=[], answer="No relevant documents found.", total_found=0
            )

        # Process results
        formatted_results = []
        for idx, (doc, metadata, distance) in enumerate(
            zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            )
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

        # Prepare context for GPT-4
        context = "\n\n".join(
            [
                f"Document {r.rank} (Similarity: {r.similarity:.2%}):\n{r.chunk}"
                for r in formatted_results
            ]
        )

        logger.debug(f"""Context for GPT-4:\n{context}""")

        # Query GPT-4
        prompt = f"""Below are several excerpts from legal documents retrieved
        based on the query:\n:
        ------\n{context}\n------\n

        Based on the above context (if relevant), please provide a clear
        and concise answer to the following legal question:\n
        {request.query_text}\n\n

        If none of the provided context is relevant, please state that no
        clear answer could be determined from the available documents.
        """

        try:
            # Make async API call
            chat_completion = await client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,  # Keep it factual
            )

            answer = chat_completion.choices[0].message.content

        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}")
            raise HTTPException(
                status_code=500, detail=f"Failed to generate answer: {str(e)}"
            )

        return RagResponse(
            context=formatted_results,
            answer=answer,
            total_found=len(formatted_results),
        )

    except Exception as e:
        logger.error(f"RAG search failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"RAG search failed: {str(e)}")


def get_document_path(source: str) -> Path:
    """Get the full path to a document from its source identifier.

    Args:
        source: Source path from metadata

    Returns:
        Path: Full path to the document

    Raises:
        ValueError: If source path is invalid
    """
    try:
        # Get the configured documents root directory
        docs_root = get_docs_root()

        # Convert source to Path and resolve against docs root
        doc_path = Path(source)
        if not doc_path.is_absolute():
            doc_path = docs_root / doc_path

        # Ensure the resolved path is within docs_root for security
        try:
            doc_path.relative_to(docs_root)
        except ValueError:
            raise ValueError(
                f"Document path {doc_path} is outside docs root {docs_root}"
            )

        return doc_path
    except Exception as e:
        raise ValueError(f"Invalid source path: {source}") from e


def load_document_content(path: Path) -> str:
    """Load the full content of a document.

    Args:
        path: Path to the document

    Returns:
        str: Document content

    Raises:
        FileNotFoundError: If document doesn't exist
        IOError: If document can't be read
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Document not found: {path}")
    except IOError as e:
        raise HTTPException(status_code=500, detail=f"Failed to read document: {e}")


@app.get(
    "/api/documents/{document_id}", response_model=DocumentResponse, tags=["Documents"]
)
async def get_document(document_id: str) -> DocumentResponse:
    """Retrieve a full document by its ID.

    This endpoint returns the complete content of a document along with its metadata
    and the list of chunks used for search.

    Args:
        document_id: Document identifier from metadata.source

    Returns:
        DocumentResponse containing the full document and metadata

    Raises:
        HTTPException: If document is not found or can't be accessed
    """
    try:
        # Query Chroma to get all chunks for this document
        results = collection.query(
            query_texts=[""],  # Empty query to match all
            where={"source": document_id},
            include=["documents", "metadatas"],
        )

        if not results or not results["documents"]:
            raise HTTPException(
                status_code=404, detail=f"Document not found in index: {document_id}"
            )

        # Get document path from first chunk's metadata
        doc_path = get_document_path(document_id)

        # Load full document content
        content = load_document_content(doc_path)

        # Return response with full content and metadata
        return DocumentResponse(
            content=content,
            metadata=results["metadatas"][0],  # First chunk's metadata
            source=document_id,
            chunks=results["documents"][0],  # All chunks from this document
        )

    except Exception as e:
        logger.error(f"Error retrieving document {document_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve document: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
