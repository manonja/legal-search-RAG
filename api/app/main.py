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

import logging
import uvicorn
import sentry_sdk

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers.health import router as health_router
from app.routers.documents.upload import router as documents_router
from app.routers.documents.query import router as query_router
from app.routers.documents.search import router as search_router
from app.routers.documents.document import router as document_router
from app.services.startup import initialize_application

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

# Get application settings
settings = get_settings()

# Initialize Sentry only if not in test environment
if not os.getenv("TESTING"):
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        # Add data like request headers and IP for users,
        # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
        send_default_pii=True,
    )

# Initialize FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Mount routers
app.include_router(health_router, prefix=settings.API_PREFIX)
app.include_router(documents_router, prefix=settings.API_PREFIX)
app.include_router(query_router, prefix=settings.API_PREFIX)
app.include_router(search_router, prefix=settings.API_PREFIX)
app.include_router(document_router, prefix=settings.API_PREFIX)


@app.on_event("startup")
async def startup_event():
    """Initialize components on application startup."""
    await initialize_application()


if __name__ == "__main__":
    port = int(os.getenv("API_PORT", 8000))
    host = os.getenv("HOST", "127.0.0.1")  # Default to localhost instead of 0.0.0.0

    logger.info(f"Starting API server on {host}:{port}")
    uvicorn.run("app.main:app", host=host, port=port, reload=True)
