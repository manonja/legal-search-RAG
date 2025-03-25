"""FastAPI service for legal document RAG system.

This module provides REST API endpoints to interact with the
Chroma vector database.
"""

import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import uvicorn

# Import from local modules - only keep what we have
from auth.auth import router as auth_router
from dotenv import load_dotenv
from fastapi import Body, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Constants
TENANT_ID = os.getenv("TENANT_ID", "default")
API_VERSION = "1.0.0"

# Models for search functionality
class QueryRequest(BaseModel):
    """Request model for document search queries."""
    query_text: str = Field(..., min_length=1, description="The text to search for")
    n_results: int = Field(default=3, ge=1, le=20, description="Number of results to return")
    min_similarity: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum similarity threshold (0 to 1)")
    metadata_filter: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata filters")

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
    min_similarity: Optional[float] = Field(0.7, description="Minimum similarity threshold (0-1)")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for follow-up questions")
    messages: Optional[List[Dict[str, str]]] = Field(None, description="Message history for the conversation")
    metadata_filter: Optional[Dict[str, Any]] = Field(None, description="Metadata filter for document search")

class RagResponse(BaseModel):
    """Response model for RAG search and answer generation."""
    answer: str = Field(..., description="The generated answer")
    source_documents: List[SourceDocument] = Field(..., description="Source documents used for context")
    conversation_id: str = Field(..., description="Conversation ID for follow-up questions")
    usage: Optional[UsageInfo] = Field(None, description="Usage information for the API call")

# Initialize FastAPI app with metadata
app = FastAPI(
    title="Legal Document Search API",
    description="API for legal document processing and search with tenant isolation",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to frontend domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include just the auth router
app.include_router(auth_router)

@app.get("/api/health", tags=["System"])
async def health_check():
    """Check API health and version."""
    return {
        "status": "ok",
        "version": API_VERSION,
        "tenant_id": TENANT_ID,
    }

@app.get("/api/tenant-info")
async def tenant_info(request: Request):
    """Get information about the current tenant."""
    return {
        "tenant_id": TENANT_ID,
        "api_version": API_VERSION,
        "gcp_credentials": os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "Not set")
    }

# Simple mock data for development
MOCK_DOCUMENTS = [
    {
        "chunk": "Summary judgment is a procedural device used during civil litigation to promptly dispose of a case without a trial. It is used when there is no dispute as to the material facts of the case and a party is entitled to judgment as a matter of law.",
        "metadata": {"source": "legal_summary.pdf", "page": 1},
        "similarity": 0.92
    },
    {
        "chunk": "Hearsay evidence is testimony from a witness under oath who is reciting an out-of-court statement that is being offered to prove the truth of the matter asserted. In general, courts exclude hearsay evidence in trial, subject to many exceptions.",
        "metadata": {"source": "evidence_rules.pdf", "page": 42},
        "similarity": 0.85
    },
    {
        "chunk": "The objection process during trial involves raising an issue with testimony or evidence that violates the rules of evidence or procedure. Common objections include relevance, hearsay, or leading the witness.",
        "metadata": {"source": "trial_advocacy.pdf", "page": 103},
        "similarity": 0.78
    }
]

@app.post("/api/search", response_model=QueryResponse, tags=["Search"])
async def search_documents(request: QueryRequest):
    """Search for relevant document chunks (simplified mock implementation)."""
    logger.info(f"Search query: {request.query_text}")

    # Filter results based on similarity threshold
    filtered_results = [
        doc for doc in MOCK_DOCUMENTS
        if doc["similarity"] >= request.min_similarity
    ][:request.n_results]

    # Format results
    results = [
        SearchResult(
            chunk=doc["chunk"],
            metadata=doc["metadata"],
            similarity=doc["similarity"],
            rank=i+1
        )
        for i, doc in enumerate(filtered_results)
    ]

    return QueryResponse(
        results=results,
        total_found=len(results)
    )

@app.post("/api/rag-search", response_model=RagResponse, tags=["Search"])
async def rag_search(request: RagRequest):
    """Search and generate answer (simplified mock implementation)."""
    logger.info(f"RAG search query: {request.query}")

    # Generate conversation ID if not provided
    conversation_id = request.conversation_id or str(uuid.uuid4())

    # Mock answer based on query
    if "summary judgment" in request.query.lower():
        answer = "# Summary Judgment\n\nSummary judgment is a procedural device used during civil litigation to promptly dispose of a case without a trial. It is appropriate when there is no genuine dispute as to any material fact.\n\n## Key Points:\n- Can be requested by either plaintiff or defendant\n- Requires no disputed material facts\n- Decision is made as a matter of law\n- Saves time and resources of a full trial\n\nFor more details, see [Federal Rules of Civil Procedure, Rule 56](source:legal_summary.pdf)."
    elif "hearsay" in request.query.lower():
        answer = "# Hearsay Evidence\n\nHearsay is an out-of-court statement offered to prove the truth of the matter asserted. It is generally inadmissible, but has numerous exceptions.\n\n## Key Exceptions:\n- Present sense impression\n- Excited utterance\n- Business records\n- Dying declaration\n\nThe Federal Rules of Evidence (FRE) contains over 30 exceptions to the hearsay rule. For more information, see [Federal Rules of Evidence 801-807](source:evidence_rules.pdf)."
    elif "objection" in request.query.lower():
        answer = "# Trial Objections\n\nObjections are formal protests raised during proceedings when a question, exhibit, or other evidence violates rules of evidence or procedure.\n\n## Common Objections:\n- Relevance\n- Hearsay\n- Leading the witness\n- Speculation\n- Assumes facts not in evidence\n\nFor more detailed information about proper objection technique, see [Trial Advocacy Handbook](source:trial_advocacy.pdf)."
    else:
        answer = "I don't have specific information about that legal topic in my knowledge base. Please try another query related to summary judgment, hearsay evidence, or trial objections."

    # Mock source documents
    source_docs = [
        SourceDocument(
            content=doc["metadata"]["source"],
            metadata=doc["metadata"],
            similarity=doc["similarity"]
        )
        for doc in MOCK_DOCUMENTS[:2]
    ]

    # Mock usage info
    usage = UsageInfo(
        input_tokens=len(request.query.split()) * 2,
        output_tokens=len(answer.split()) * 2,
        total_tokens=(len(request.query.split()) + len(answer.split())) * 2,
        cost=0.002
    )

    return RagResponse(
        answer=answer,
        source_documents=source_docs,
        conversation_id=conversation_id,
        usage=usage
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Global exception handler for the API."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Server error: {str(exc)}"},
    )

if __name__ == "__main__":
    # Run the API server directly when the script is executed
    uvicorn.run("api:app", host="0.0.0.0", port=8080, reload=True)
