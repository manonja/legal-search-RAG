"""FastAPI service for legal document RAG system.

This module provides REST API endpoints for Retool to interact with the
Chroma vector database.
"""

import hashlib
import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, TypeVar, cast

import chromadb
import uvicorn
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

# Import from local modules
from api_modules.admin import router as admin_router
from middleware.cost_control import CostControlMiddleware
from utils.env import get_docs_root
from utils.usage_db import init_usage_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Add a filter to suppress ChromaDB warnings about existing embedding IDs
class ChromaWarningFilter(logging.Filter):
    """Filter to suppress specific ChromaDB warnings about existing embedding IDs."""

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
EMBEDDING_MODEL = "text-embedding-ada-002"  # Updated to latest model
CHROMA_PERSIST_DIR = os.path.join(os.path.dirname(__file__), "cache", "chroma")
DOCUMENTS_DIR = os.getenv(
    "DOCUMENTS_DIR", os.path.join(os.path.dirname(__file__), "..", "data")
)
CACHE_PATH = os.path.join(os.path.dirname(__file__), "cache", "query_cache.json")
COLLECTION_NAME = "legal_docs"
API_VERSION = "1.0.0"

# S3 configuration (for cloud deployment)
USE_S3_STORAGE = os.getenv("USE_S3_STORAGE", "false").lower() == "true"
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "")
S3_PREFIX = os.getenv("S3_PREFIX", "legal-search-data")
AWS_REGION = os.getenv("AWS_REGION", "us-west-2")

# Type variables
T = TypeVar("T", bound=BaseModel)


def initialize_chroma_client():
    """Initialize ChromaDB client based on environment configuration.

    Returns:
        chromadb.Client: Configured client for either local or S3 storage
    """
    logger.info("Initializing Chroma client")

    if USE_S3_STORAGE and S3_BUCKET_NAME:
        try:
            import boto3
            from chromadb.config import Settings

            logger.info(f"Using S3 storage: s3://{S3_BUCKET_NAME}/{S3_PREFIX}")

            # Configure S3 persistence settings
            settings = Settings(
                chroma_api_impl="rest",
                chroma_server_host="localhost",
                chroma_server_http_port=8000,
                anonymized_telemetry=False,
                allow_reset=True,
                persist_directory=CHROMA_PERSIST_DIR,  # Temporary local cache
            )

            # Create the client with S3 persistence
            chroma_dir = Path(CHROMA_PERSIST_DIR)
            chroma_dir.mkdir(parents=True, exist_ok=True)

            # Configure S3 client
            s3_client = boto3.client(
                "s3",
                region_name=AWS_REGION,
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            )

            return chromadb.PersistentClient(path=str(chroma_dir), settings=settings)

        except ImportError:
            logger.warning("boto3 not installed, falling back to local storage")
            # Fall back to local storage if boto3 is not available

    # Default to local storage
    logger.info(f"Using local storage: {CHROMA_PERSIST_DIR}")
    chroma_dir = Path(CHROMA_PERSIST_DIR)
    chroma_dir.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(chroma_dir))


# Process a document and add its chunks to the collection
def process_document(doc_path: Path) -> None:
    """Process a document and add its chunks to Chroma.

    Args:
        doc_path: Path to the document file
    """
    try:
        # Get document name from path
        doc_name = doc_path.stem.replace("chunked_", "")
        logger.info(f"Processing document: {doc_name}")

        # Read document content
        with open(doc_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Split into chunks (assuming document is pre-chunked and separated by markers)
        chunks = content.split("\n\n--- CHUNK ---\n\n")
        if len(chunks) == 1:  # No markers, treat as a single chunk
            chunks = [content]

        # Prepare data for Chroma
        chunk_ids = []
        chunk_texts = []
        chunk_metadatas = []

        # Process each chunk
        for i, chunk in enumerate(chunks):
            if not chunk.strip():
                continue

            # Generate a unique ID for this chunk
            chunk_id = (
                f"{doc_name}_chunk_{i+1}"  # Start from 1 instead of 0 for consistency
            )

            # Add to batch
            chunk_ids.append(chunk_id)
            chunk_texts.append(chunk)
            chunk_metadatas.append(
                {
                    "filename": str(
                        doc_path
                    ),  # Changed from 'source' to 'filename' to match existing format
                    "chunk_index": i,
                }
            )

        # Use upsert instead of add to avoid duplicate ID warnings
        if chunk_ids:
            collection.upsert(
                ids=chunk_ids,
                documents=chunk_texts,
                metadatas=chunk_metadatas,
            )
            logger.info(f"Upserted {len(chunk_ids)} chunks from {doc_name}")

    except Exception as e:
        logger.error(f"Error processing document {doc_path}: {e}")
        logger.exception(e)  # Log full traceback for debugging


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

# Add cost control middleware
app.add_middleware(CostControlMiddleware)

# Include admin router
app.include_router(admin_router)


# Initialize usage database
@app.on_event("startup")
async def startup_event():
    """Initialize components on application startup."""
    try:
        # Initialize usage database
        init_usage_db()
        logger.info("Usage database initialized")
    except Exception as e:
        logger.error(f"Error initializing usage database: {e}")


try:
    # Initialize OpenAI embedding function
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=os.getenv("OPENAI_API_KEY"),
        model_name=EMBEDDING_MODEL,
    )

    # Initialize Chroma client and collection
    logger.info("Initializing Chroma client and collection")
    client = initialize_chroma_client()

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
    except ValueError:
        # Only create collection if it doesn't exist
        logger.info(f"Creating new collection '{COLLECTION_NAME}'")
        collection = client.create_collection(
            name=COLLECTION_NAME,
            embedding_function=openai_ef,
            metadata={"hnsw:space": "cosine"},
        )

        # Load documents and create embeddings only for new collection
        documents_dir = Path(DOCUMENTS_DIR)
        if documents_dir.exists():
            for doc_file in documents_dir.glob("chunked_*.txt"):
                # Process each document file
                process_document(doc_file)

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

# Initialize cache directories
os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)


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


class SourceDocument(BaseModel):
    """Source document model with metadata."""

    content: str = Field(..., description="Document content or title")
    metadata: Dict[str, Any] = Field(..., description="Document metadata")
    similarity: float = Field(..., description="Similarity score (0-1)")


class UsageInfo(BaseModel):
    """Usage information for an API call."""

    input_tokens: int = Field(..., description="Number of input tokens used")
    output_tokens: int = Field(..., description="Number of output tokens generated")
    total_tokens: int = Field(..., description="Total tokens used")
    cost: float = Field(..., description="Estimated cost of the API call")


class RagRequest(BaseModel):
    """Request model for RAG search and answer generation."""

    query: str = Field(..., description="The query text to search for")
    model: Optional[str] = Field("gpt-4", description="The OpenAI model to use")
    temperature: Optional[float] = Field(0.0, description="Temperature for generation")
    max_tokens: Optional[int] = Field(1000, description="Maximum tokens to generate")
    n_results: Optional[int] = Field(5, description="Number of results to return")
    min_similarity: Optional[float] = Field(
        0.7, description="Minimum similarity threshold (0-1)"
    )
    conversation_id: Optional[str] = Field(
        None, description="Conversation ID for follow-up questions"
    )
    messages: Optional[List[Dict[str, str]]] = Field(
        None, description="Message history for the conversation"
    )
    metadata_filter: Optional[Dict[str, Any]] = Field(
        None, description="Metadata filter for document search"
    )


class RagResponse(BaseModel):
    """Response model for RAG search and answer generation."""

    answer: str = Field(..., description="The generated answer")
    source_documents: List[SourceDocument] = Field(
        ..., description="Source documents used for context"
    )
    conversation_id: str = Field(
        ..., description="Conversation ID for follow-up questions"
    )
    usage: Optional[UsageInfo] = Field(
        None, description="Usage information for the API call"
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


def get_query_hash(request: RagRequest) -> str:
    """Generate a hash for the query to use as a cache key.

    Args:
        request: The RAG request object

    Returns:
        A hash string representing the query
    """
    # Include relevant parameters that affect the result
    query_params = {
        "query": request.query,
        "model": request.model,
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
        "n_results": request.n_results,
        "min_similarity": request.min_similarity,
        "metadata_filter": request.metadata_filter,
    }
    # Convert to string and hash
    param_str = json.dumps(query_params, sort_keys=True)
    return hashlib.md5(param_str.encode()).hexdigest()


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
    return (datetime.now() - cache_time).total_seconds() < 86400  # 24 hours


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
async def rag_search(request: RagRequest) -> RagResponse:
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

        # Generate a conversation ID if not provided
        if not request.conversation_id:
            request.conversation_id = str(uuid.uuid4())

        logger.info(f"Processing RAG search request: {request.query}")

        # Check cache first
        query_hash = get_query_hash(request)
        cached_result = query_cache.get(query_hash)
        if cached_result and is_cache_valid(cached_result):
            logger.info("Returning cached result")
            return RagResponse(**cached_result["data"])

        # Query Chroma with optimized parameters
        results = collection.query(
            query_texts=[request.query],
            n_results=request.n_results,
            where=request.metadata_filter,
            include=["documents", "metadatas", "distances"],
        )

        if not results or not results.get("documents"):
            logger.warning("No results found for query")
            return RagResponse(
                answer="No relevant documents found.",
                source_documents=[],
                conversation_id=request.conversation_id,
                usage=None,
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
            f"{request.query}\n\n"
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
                model=request.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )

            answer = chat_completion.choices[0].message.content

            # Cache the result
            response_data = {
                "answer": answer,
                "source_documents": [
                    SourceDocument(
                        content=source.title,
                        metadata={"filename": source.source},
                        similarity=source.similarity,
                    )
                    for source in document_sources.values()
                ],
                "conversation_id": request.conversation_id,
                "usage": {
                    "input_tokens": chat_completion.usage.prompt_tokens,
                    "output_tokens": chat_completion.usage.completion_tokens,
                    "total_tokens": chat_completion.usage.total_tokens,
                    "cost": chat_completion.usage.total_tokens
                    * 0.000002,  # Assuming $0.000002 per token
                },
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


async def get_document_content(document_id: str) -> tuple[str, dict]:
    """Get document content and metadata from either local storage or S3.

    Args:
        document_id: Document identifier (filename)

    Returns:
        Tuple of (document content, metadata dictionary)

    Raises:
        FileNotFoundError: If document cannot be found
        IOError: If document cannot be read
    """
    if USE_S3_STORAGE and S3_BUCKET_NAME:
        try:
            import boto3

            # Initialize S3 client
            s3_client = boto3.client(
                "s3",
                region_name=AWS_REGION,
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            )

            # First check if the document exists with the given ID
            try:
                key = f"{S3_PREFIX}/documents/{document_id}"
                logger.info(f"Attempting to fetch document from S3: {key}")
                response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=key)
                content = response["Body"].read().decode("utf-8")
                metadata = response.get("Metadata", {})
                metadata["filename"] = document_id
                metadata["source"] = f"s3://{S3_BUCKET_NAME}/{key}"
                return content, metadata
            except s3_client.exceptions.NoSuchKey:
                # Try with chunked_ prefix
                key = f"{S3_PREFIX}/documents/chunked_{document_id}"
                try:
                    logger.info(f"Attempting to fetch chunked document from S3: {key}")
                    response = s3_client.get_object(Bucket=S3_BUCKET_NAME, Key=key)
                    content = response["Body"].read().decode("utf-8")
                    metadata = response.get("Metadata", {})
                    metadata["filename"] = document_id
                    metadata["source"] = f"s3://{S3_BUCKET_NAME}/{key}"
                    return content, metadata
                except s3_client.exceptions.NoSuchKey:
                    logger.warning(f"Document not found in S3: {document_id}")
                    # Fall back to local storage
        except ImportError:
            logger.warning("boto3 not installed, falling back to local storage")
        except Exception as e:
            logger.error(f"Error accessing S3: {str(e)}")
            # Fall back to local storage if there's an S3 error

    # Default to local storage access
    try:
        doc_path = get_document_path(document_id)
        with open(doc_path, "r", encoding="utf-8") as f:
            content = f.read()
        metadata = {"filename": doc_path.name, "source": str(doc_path)}
        return content, metadata
    except FileNotFoundError:
        raise
    except Exception as e:
        raise IOError(f"Failed to read document: {str(e)}")


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
            raise HTTPException(status_code=404, detail=str(e))
        except IOError as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to read document: {str(e)}"
            )

        # Return document response
        return DocumentResponse(
            content=content,
            metadata=metadata,
            source=metadata.get("source", ""),
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
