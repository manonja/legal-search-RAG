"""FastAPI service for legal document RAG system.

This module provides REST API endpoints for Retool to interact with the
Chroma vector database.
"""

import hashlib
import logging
import os
from datetime import datetime, timedelta
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

# Cache for storing query results
query_cache: Dict[str, Dict] = {}
CACHE_DURATION = timedelta(hours=24)  # Cache duration for query results


# Request/Response Models
class QueryRequest(BaseModel):
    """Request model for document search queries."""

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


class DocumentSource(BaseModel):
    """Model representing a document source with metadata."""

    source: str = Field(..., description="Document source path")
    title: str = Field(..., description="Document title")
    similarity: float = Field(..., description="Similarity score (0 to 1)")


class RagResponse(BaseModel):
    """Response model for RAG-enhanced search queries."""

    context: List[SearchResult] = Field(..., description="Retrieved context documents")
    answer: str = Field(..., description="GPT-4 generated answer")
    total_found: int = Field(..., description="Total number of context documents found")
    document_sources: List[DocumentSource] = Field(
        ..., description="List of unique document sources"
    )


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


def get_query_hash(query_text: str) -> str:
    """Generate a hash for the query text to use as cache key."""
    return hashlib.md5(query_text.encode()).hexdigest()


def is_cache_valid(cache_entry: Dict) -> bool:
    """Check if a cache entry is still valid."""
    if not cache_entry:
        return False
    cache_time = datetime.fromisoformat(cache_entry.get("timestamp", ""))
    return datetime.now() - cache_time < CACHE_DURATION


async def process_document_chunk(
    chunk: Dict, collection: chromadb.Collection
) -> Optional[Dict]:
    """Process a single document chunk asynchronously."""
    try:
        # Extract metadata
        metadata = chunk.get("metadata", {})
        source = metadata.get("source", "")
        title = metadata.get("title", "")
        similarity = chunk.get("distance", 0.0)

        # Get the document content
        content = chunk.get("document", "")

        return {
            "source": source,
            "title": title,
            "similarity": similarity,
            "content": content,
        }
    except Exception as e:
        logger.error(f"Error processing document chunk: {e}")
        return None


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

        # Check cache first
        query_hash = get_query_hash(request.query_text)
        cached_result = query_cache.get(query_hash)
        if cached_result and is_cache_valid(cached_result):
            logger.info("Returning cached result")
            return RagResponse(**cached_result["data"])

        # Query Chroma with optimized parameters
        results = collection.query(
            query_texts=[request.query_text],
            n_results=request.n_results,
            where=request.metadata_filter,
            include=["documents", "metadatas", "distances"],
        )

        if not results or not results.get("documents"):
            logger.warning("No results found for query")
            return RagResponse(
                context=[],
                answer="No relevant documents found.",
                total_found=0,
                document_sources=[],
            )

        # Process results
        formatted_results = []
        document_sources = {}  # Use dict to track unique sources
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

            # Create search result
            result = SearchResult(
                chunk=doc,
                metadata=cast(Dict[str, Any], metadata),
                similarity=similarity,
                rank=idx + 1,
            )
            formatted_results.append(result)

            # Track document sources
            source = metadata.get("source", "Unknown Document")
            if (
                source not in document_sources
                or similarity > document_sources[source].similarity
            ):
                document_sources[source] = DocumentSource(
                    source=source,
                    title=metadata.get("title", source),
                    similarity=similarity,
                )

        # Prepare context for GPT-4
        context = "\n\n".join(
            [
                (
                    f"Document {r.rank} (Similarity: {r.similarity:.2%}):\n"
                    f"Source: {r.metadata.get('source', 'Unknown Document')}\n"
                    f"{r.chunk}"
                )
                for r in formatted_results
            ]
        )

        logger.debug(f"""Context for GPT-4:\n{context}""")

        # Query GPT-4 with optimized prompt
        system_message = (
            "You are a legal research assistant providing answers based on the "
            "provided legal documents.\nYour responses should be comprehensive but "
            "concise, including:\n1. A brief summary (2-3 sentences)\n2. Key legal "
            "concepts (bullet points)\n3. Relevant case law (if mentioned)\n4. "
            "Practical considerations (if applicable)\n5. Source attribution with "
            "clickable links\n\n"
            "Format your response in markdown with appropriate headers. For each "
            "source you reference, include a clickable link using the format:\n"
            "[Source Name](source:filename.txt)\n\n"
            'For example, if you reference information from "Medical Malpractice '
            'Guide.txt", include a link like:\n'
            "[Medical Malpractice Guide](source:Medical Malpractice Guide.txt)\n\n"
            "This will allow users to click directly on the source to view the "
            "full document."
        )

        user_prompt = (
            "Based on the following legal document excerpts, please provide a "
            "concise answer to this legal question:\n\n"
            f"{request.query_text}\n\n"
            "Document excerpts:\n"
            "------\n"
            f"{context}\n"
            "------\n\n"
            "Please structure your response to be clear and concise, focusing on "
            "the most relevant information. Include clickable links to the source "
            "documents where you reference them."
        )

        try:
            # Make async API call with optimized parameters
            chat_completion = await client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.0,
                max_tokens=1000,  # Limit response length
            )

            answer = chat_completion.choices[0].message.content

            # Cache the result
            response_data = {
                "context": [
                    result.dict() for result in formatted_results
                ],  # Convert SearchResult objects to dicts
                "answer": answer,
                "total_found": len(formatted_results),
                "document_sources": [
                    source.dict() for source in document_sources.values()
                ],
            }
            query_cache[query_hash] = {
                "data": response_data,
                "timestamp": datetime.now().isoformat(),
            }

            return RagResponse(**response_data)

        except Exception as e:
            logger.error(f"Error in GPT-4 API call: {e}")
            raise HTTPException(status_code=500, detail="Error generating response")

    except Exception as e:
        logger.error(f"Error in rag_search: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def get_document_path(document_id: str) -> Path:
    """Get the full path to a document from its ID.

    Args:
        document_id: Document identifier (filename)

    Returns:
        Path to the processed document
    """
    # Remove any URL encoding
    document_id = document_id.replace("%20", " ")

    logger.info(f"Looking for document: {document_id}")

    # Look in processed docs directory first
    docs_root = Path(get_docs_root())
    logger.info(f"Searching in processed docs directory: {docs_root}")

    # First try the exact path if it exists
    if (docs_root / document_id).exists():
        logger.info(f"Found document at exact path: {docs_root / document_id}")
        return docs_root / document_id

    # Then try finding it by name only, including in subdirectories
    for file in docs_root.rglob("*"):
        if file.name == document_id:
            logger.info(f"Found document by name: {file}")
            return file

    # If not found in processed docs, look in chunked docs directory
    chunks_dir = Path(
        os.getenv("CHUNKS_DIR", os.path.expanduser("~/Downloads/chunkedLegalDocs"))
    )
    logger.info(f"Searching in chunked docs directory: {chunks_dir}")

    # First try the exact path if it exists
    if (chunks_dir / document_id).exists():
        logger.info(f"Found document at exact path: {chunks_dir / document_id}")
        return chunks_dir / document_id

    # Then try finding it by name only, including in subdirectories
    for file in chunks_dir.rglob("*"):
        if file.name == document_id:
            logger.info(f"Found document by name: {file}")
            return file

    # If we get here, we didn't find the document
    logger.error(f"Document not found: {document_id}")
    raise FileNotFoundError(f"Document not found: {document_id}")


@app.get(
    "/api/documents/{document_id}", response_model=DocumentResponse, tags=["Documents"]
)
async def get_document(document_id: str) -> DocumentResponse:
    """Retrieve a full document by its ID.

    Args:
        document_id: Document identifier (filename)

    Returns:
        DocumentResponse containing the full document and metadata

    Raises:
        HTTPException: If document is not found or can't be accessed
    """
    try:
        # Get the document path
        try:
            doc_path = get_document_path(document_id)
        except FileNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e))

        # Load full document content
        try:
            with open(doc_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to read document: {str(e)}"
            )

        # Return document response
        return DocumentResponse(
            content=content,
            metadata={"filename": doc_path.name},
            source=str(doc_path),
            chunks=[],  # Empty chunks since we're not using Chroma here
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve document: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True, log_level="info")
