"""FastAPI service for legal document RAG system.

This module provides REST API endpoints to interact with the
Chroma vector database.
"""

# Disable ChromaDB telemetry before any imports
import os

# Set environment variables to disable telemetry
os.environ["ANONYMIZED_TELEMETRY"] = "FALSE"
os.environ["CHROMADB_TELEMETRY_ENABLED"] = "FALSE"
os.environ["OPENTELEMETRY_ENABLED"] = "FALSE"

# Patch sys.modules to prevent OpenTelemetry imports from failing
import sys


class DisabledModule:
    """A module that returns None for any attribute access."""

    def __getattr__(self, name):
        return None


# Create fake modules for problematic imports
for module_name in [
    "opentelemetry.exporter.otlp.proto.grpc.trace_exporter",
    "opentelemetry.exporter.otlp.proto.grpc.exporter",
    "opentelemetry.sdk.resources",
    "opentelemetry.sdk.trace",
    "opentelemetry.sdk.trace.export",
    "opentelemetry.trace",
    "grpc",
]:
    if module_name not in sys.modules:
        sys.modules[module_name] = DisabledModule()

import hashlib
import json
import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, TypeVar, cast

# Import other dependencies after setting environment variables
import chromadb
import uvicorn
from chromadb.config import Settings
from chromadb.errors import InvalidCollectionException
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from middleware.cost_control import CostControlMiddleware
from openai import AsyncOpenAI
from pydantic import BaseModel, Field
from utils.env import get_chroma_dir, get_chunks_dir, get_docs_root
from utils.usage_db import init_usage_db, record_usage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Add a filter to suppress ChromaDB warnings about existing embedding IDs
class ChromaWarningFilter(logging.Filter):
    """A filter to remove specific ChromaDB warnings."""

    def filter(self, record):
        """Filter out warnings about adding existing embedding IDs.

        Args:
            record: The log record to check

        Returns:
            bool: False for messages to be filtered out, True otherwise
        """
        # Filter out the specific warning about adding existing embedding IDs
        return not (
            record.levelname == "WARNING"
            and "Add of existing embedding ID:" in record.getMessage()
        )


# Apply the filter to the ChromaDB logger
chroma_logger = logging.getLogger("chromadb.segment.impl.vector.local_persistent_hnsw")
chroma_logger.addFilter(ChromaWarningFilter())

# Load environment variables
load_dotenv()

# Constants
EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002")
DOCUMENTS_DIR = os.getenv(
    "DOCUMENTS_DIR", os.path.join(os.path.dirname(__file__), "..", "data")
)
CACHE_PATH = os.path.join(os.path.dirname(__file__), "cache", "query_cache.json")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "legal_docs")
API_VERSION = "1.0.0"

# Type variables
T = TypeVar("T", bound=BaseModel)


def initialize_chroma_client():
    """Initialize ChromaDB client based on environment configuration.

    Returns:
        chromadb.Client: Configured client for local storage
    """
    logger.info("Initializing Chroma client")

    # Get ChromaDB directory
    chroma_dir = get_chroma_dir()

    logger.info(f"Using local ChromaDB storage: {chroma_dir}")

    # Create client with telemetry disabled
    return chromadb.PersistentClient(
        path=str(chroma_dir),
        settings=Settings(
            anonymized_telemetry=False,  # Disable telemetry
            allow_reset=True,
            is_persistent=True,
        ),
    )


# Initialize FastAPI app with metadata
app = FastAPI(
    title="Legal Document Search API",
    description="API for searching legal documents using semantic similarity",
    version=API_VERSION,
    docs_url="/",  # Swagger UI at root endpoint
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local development
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Add cost control middleware
app.add_middleware(CostControlMiddleware)


# Initialize usage database
@app.on_event("startup")
async def startup_event():
    """Initialize components on application startup."""
    try:
        # Initialize usage database
        init_usage_db()
        logger.info("Usage database initialized")

        # Initialize cache directories
        os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
        logger.info(f"Cache directory created at {os.path.dirname(CACHE_PATH)}")
    except Exception as e:
        logger.error(f"Error during initialization: {e}")


# Initialize OpenAI client
client = AsyncOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    timeout=60.0,  # Increase timeout for longer responses
)

# Cache for storing query results
query_cache: Dict[str, Dict] = {}
CACHE_DURATION = timedelta(hours=24)  # Cache duration for query results

try:
    # Initialize OpenAI embedding function
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name=EMBEDDING_MODEL,
    )

    # Initialize Chroma client and collection with a retry mechanism
    logger.info("Initializing Chroma client and collection")
    max_attempts = 3
    attempt = 0
    client = None

    while attempt < max_attempts:
        try:
            attempt += 1
            logger.info(f"ChromaDB initialization attempt {attempt}/{max_attempts}")
            client = initialize_chroma_client()
            # Test connection with a simple operation
            client.list_collections()
            break
        except Exception as e:
            logger.warning(f"ChromaDB initialization attempt {attempt} failed: {e}")
            if attempt >= max_attempts:
                raise
            import time

            time.sleep(1)  # Wait before retrying

    # Check if collection exists before creating it
    try:
        collection = client.get_collection(
            COLLECTION_NAME, embedding_function=openai_ef
        )
        logger.info(
            f"Collection '{COLLECTION_NAME}' already exists with "
            f"{collection.count()} embeddings"
        )
        # Skip document loading for existing collections
    except (ValueError, InvalidCollectionException):
        # Only create collection if it doesn't exist
        logger.info(f"Creating new collection '{COLLECTION_NAME}'")
        collection = client.create_collection(
            name=COLLECTION_NAME,
            embedding_function=openai_ef,
            metadata={"hnsw:space": "cosine"},
        )

    logger.info("Successfully initialized Chroma client and collection")

except Exception as e:
    logger.error(f"Error initializing Chroma: {e}")
    logger.exception(e)  # Log full traceback for debugging


# Define API Models
class SearchQuery(BaseModel):
    """Search query parameters for basic vector search."""

    query: str = Field(..., description="Search query text")
    limit: int = Field(5, description="Maximum number of results to return")


class SearchResult(BaseModel):
    """Search result model."""

    text: str = Field(..., description="Document chunk text")
    metadata: Dict[str, Any] = Field(..., description="Document metadata")
    distance: float = Field(..., description="Similarity distance")


class RAGQuery(BaseModel):
    """RAG query parameters for generating answers from documents."""

    query: str = Field(..., description="Question to answer")
    limit: int = Field(5, description="Maximum number of documents to retrieve")
    max_tokens: Optional[int] = Field(1000, description="Maximum tokens to generate")
    temperature: float = Field(0.7, description="Sampling temperature")


class RAGResponse(BaseModel):
    """RAG response model with answer and sources."""

    answer: str = Field(..., description="Generated answer to the question")
    sources: List[Dict[str, Any]] = Field(..., description="Source documents used")
    total_tokens: int = Field(..., description="Total tokens used")


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


class DocumentResponse(BaseModel):
    """Response model for full document retrieval."""

    content: str = Field(..., description="Full document content")
    metadata: Dict[str, Any] = Field(..., description="Document metadata")
    source: str = Field(..., description="Document source path")
    chunks: List[str] = Field(..., description="List of chunks from this document")


@app.get("/health")
async def health_check():
    """Check if the API is healthy."""
    return {"status": "ok", "version": API_VERSION}


def get_query_hash(query: str, **params) -> str:
    """Generate a hash for the query to use as a cache key.

    Args:
        query: The query text
        params: Additional parameters that affect the result

    Returns:
        A hash string representing the query
    """
    # Include relevant parameters that affect the result
    query_params = {"query": query, **params}
    # Convert to string and hash
    param_str = json.dumps(query_params, sort_keys=True)
    return hashlib.sha256(param_str.encode()).hexdigest()


def is_cache_valid(cached_result: Dict) -> bool:
    """Check if a cached result is still valid.

    Args:
        cached_result: The cached result to check

    Returns:
        True if the result is still valid, False otherwise
    """
    # Get cache timestamp
    timestamp = cached_result.get("timestamp")
    if not timestamp:
        return False

    # Parse timestamp
    try:
        cache_time = datetime.fromisoformat(timestamp)
    except ValueError:
        return False

    # Check if cache is expired (more than 24 hours old)
    return (datetime.now() - cache_time) < CACHE_DURATION


@app.post("/search", response_model=List[SearchResult])
async def search_documents(request: SearchQuery):
    """Search for documents using vector similarity.

    Args:
        request: Search query parameters

    Returns:
        List of document chunks and metadata
    """
    try:
        # Log the request
        logger.info(f"Search query: {request.query}")

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
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/search", response_model=QueryResponse, tags=["Search"])
async def legacy_search_documents(request: QueryRequest) -> QueryResponse:
    """Search for relevant document chunks using the old API format.

    This endpoint is preserved for backward compatibility.

    Args:
        request: Search parameters including query text and filters

    Returns:
        QueryResponse containing matched chunks and their metadata
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
                    text=doc,
                    metadata=cast(Dict[str, Any], metadata),
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
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}") from e


@app.post("/rag-search", response_model=RAGResponse)
async def rag_search(request: RAGQuery):
    """Generate an answer to a question using RAG.

    Args:
        request: RAG query parameters

    Returns:
        Generated answer with sources
    """
    try:
        # Check cache
        cache_key = get_query_hash(
            request.query,
            limit=request.limit,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
        )

        if cache_key in query_cache and is_cache_valid(query_cache[cache_key]):
            logger.info("Returning cached RAG result")
            cached_data = query_cache[cache_key]["data"]
            return RAGResponse(**cached_data)

        # Log the request
        logger.info(f"RAG query: {request.query}")

        # Query the collection to retrieve relevant documents
        results = collection.query(
            query_texts=[request.query],
            n_results=request.limit,
            include=["documents", "metadatas", "distances"],
        )

        # Prepare context from retrieved documents
        context = ""
        sources = []
        for i, (doc, meta, distance) in enumerate(
            zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            )
        ):
            # Add to context with a separator
            context += f"\n\nDocument {i + 1} (Distance: {distance:.4f}):\n{doc}"

            # Add to sources list
            sources.append(
                {
                    "text": doc[:200] + "..." if len(doc) > 200 else doc,
                    "metadata": meta,
                    "distance": float(distance),
                }
            )

        # Initialize OpenAI client
        openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Prepare the prompt for the language model
        system_prompt = """You are a legal assistant that helps answer questions about legal documents.
        Use ONLY information from the provided document excerpts to answer the question.
        If the answer cannot be found in the documents, say so clearly.
        DO NOT make up information or use external knowledge.
        Cite specific sections of documents when possible."""

        user_prompt = f"""Question: {request.query}

        Context from relevant legal documents:
        {context}

        Based ONLY on the above documents, please provide a comprehensive answer to the question."""

        # Call the OpenAI API
        model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        logger.info(f"Using model: {model}")

        chat_completion = await openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

        # Get the answer from the response
        answer = chat_completion.choices[0].message.content.strip()
        total_tokens = chat_completion.usage.total_tokens

        # Record usage
        record_usage("rag-search", total_tokens, model, total_tokens * 0.000002)

        # Cache the result
        response_data = {
            "answer": answer,
            "sources": sources,
            "total_tokens": total_tokens,
        }

        query_cache[cache_key] = {
            "data": response_data,
            "timestamp": datetime.now().isoformat(),
        }

        # Return the RAG response
        return RAGResponse(**response_data)

    except Exception as e:
        logger.error(f"Error during RAG search: {e}")
        logger.exception(e)  # Log full traceback for debugging
        raise HTTPException(status_code=500, detail=str(e))


async def find_document(document_id: str) -> Path:
    """Find a document by its ID in various directories.

    Args:
        document_id: Document identifier (filename)

    Returns:
        Path to the document file

    Raises:
        FileNotFoundError: If document cannot be found
    """
    # Remove any URL encoding
    document_id = document_id.replace("%20", " ")

    logger.info(f"Looking for document: {document_id}")

    # Look in processed docs directory first
    docs_root = get_docs_root()
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
    chunks_dir = get_chunks_dir()
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


async def get_document_content(document_id: str) -> tuple[str, dict]:
    """Get document content and metadata from local storage.

    Args:
        document_id: Document identifier (filename)

    Returns:
        Tuple of (document content, metadata dictionary)

    Raises:
        FileNotFoundError: If document cannot be found
        IOError: If document cannot be read
    """
    try:
        # Try to locate the document file
        doc_file = await find_document(document_id)
        logger.info(f"Found document at: {doc_file}")

        # Read the file content
        with open(doc_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Get basic metadata
        metadata = {
            "filename": doc_file.name,
            "size": doc_file.stat().st_size,
            "last_modified": datetime.fromtimestamp(
                doc_file.stat().st_mtime
            ).isoformat(),
            "source": f"local:{doc_file}",
        }

        return content, metadata
    except Exception as e:
        logger.error(f"Error reading document {document_id}: {str(e)}")
        raise


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
        # Get the document content and metadata
        try:
            content, metadata = await get_document_content(document_id)
        except FileNotFoundError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        except IOError as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to read document: {str(e)}"
            ) from e

        # Return document response
        return DocumentResponse(
            content=content,
            metadata=metadata,
            source=metadata.get("source", ""),
            chunks=[],  # Empty chunks since we're retrieving whole document
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve document: {str(e)}"
        ) from e


if __name__ == "__main__":
    port = int(os.getenv("API_PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")

    logger.info(f"Starting API server on {host}:{port}")
    uvicorn.run("api:app", host=host, port=port, reload=True)
