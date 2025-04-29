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

# Import structured logger early
from app.core.struct_logger import log

# Initialize Sentry as early as possible
import logging
import sys
import signal

import sentry_sdk
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.threading import ThreadingIntegration

# Basic logging is now configured via struct_logger.py
# Legacy logger for compatibility
legacy_logger = logging.getLogger(__name__)

# Get settings directly
from app.core.config import get_settings

settings = get_settings()

# Initialize Sentry if DSN is available and not in test mode
if not os.getenv("TESTING") == "true" and settings.SENTRY_DSN:
    log.info(
        "Initializing Sentry for environment", sentry_env=settings.SENTRY_ENVIRONMENT
    )

    # Setup integrations
    integrations = [
        FastApiIntegration(),
        LoggingIntegration(level=logging.INFO, event_level=logging.ERROR),
        ThreadingIntegration(propagate_hub=True),
        # Use AsyncioIntegration with lower traces_sample_rate for better shutdown behavior
        AsyncioIntegration(),
    ]

    # Event filtering function
    def before_send_handler(event, hint):
        """Filter events before sending to Sentry."""
        # Don't send health check endpoint events
        if event.get("request", {}).get("url", "").startswith("/api/health"):
            return None
        return event

    # Initialize Sentry SDK
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        integrations=integrations,
        enable_tracing=settings.SENTRY_ENABLE_TRACING,
        environment=settings.SENTRY_ENVIRONMENT,
        traces_sample_rate=0.05  # Reduced from previous values
        if settings.SENTRY_ENVIRONMENT.lower() == "production"
        else 0.1,  # Reduced from previous values
        profiles_sample_rate=settings.SENTRY_PROFILES_SAMPLE_RATE,
        debug=settings.DEBUG,
        send_default_pii=settings.SENTRY_SEND_PII,
        auto_enabling_integrations=False,
        attach_stacktrace=True,
        before_send=before_send_handler,
    )

    # Add app tag
    sentry_sdk.set_tag("app_name", "legal-search-rag-api")

    # Test event in non-production
    if settings.SENTRY_ENVIRONMENT.lower() != "production":
        sentry_sdk.capture_message(
            "Sentry initialized at application startup", level="info"
        )

    log.info("Sentry initialized successfully")
else:
    log.info("Sentry disabled", reason="testing or no DSN configured")
    # Disable Sentry explicitly
    sentry_sdk.init(dsn="")


# Setup graceful shutdown handler for Sentry
def handle_exit(signum, frame):
    """Handle shutdown signals gracefully."""
    log.info("Shutting down gracefully...")
    # Close Sentry client before exiting
    sentry_sdk.flush()
    # Exit with success status
    sys.exit(0)


# Register signal handlers
signal.signal(signal.SIGINT, handle_exit)
signal.signal(signal.SIGTERM, handle_exit)

# Patch sys.modules to prevent OpenTelemetry imports from failing
import types  # Add this import
from contextlib import asynccontextmanager


class DisabledModule(types.ModuleType):  # Inherit from types.ModuleType
    """A module that returns None for any attribute access."""

    def __init__(self, name):
        super().__init__(name)

    def __getattr__(self, name):
        return None


# Mock Google Cloud Secret Manager in test mode
if os.getenv("TESTING") == "true" and "google.cloud.secretmanager" not in sys.modules:
    from unittest.mock import MagicMock

    sys.modules["google.cloud"] = MagicMock()
    sys.modules["google.cloud.secretmanager"] = MagicMock()
    sys.modules["google.cloud.secretmanager_v1"] = MagicMock()

import uvicorn
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings as app_get_settings
from app.routers.documents.document import router as document_router
from app.routers.documents.query import router as query_router
from app.routers.documents.search import router as search_router
from app.routers.documents.upload import router as documents_router

# Import the dependency from the health router
from app.routers.health import auth_dependency
from app.routers.health import router as health_router
from app.services.startup import initialize_application


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

# Ensure we're using the same settings
settings = app_get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application lifespan events.

    This replaces the deprecated on_event handlers.
    """
    # Startup: initialize components
    await initialize_application()

    yield

    # Shutdown: cleanup if needed
    # No cleanup needed at the moment


# Initialize FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
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

# Mount routers using the correct dependency
app.include_router(health_router, prefix=settings.API_PREFIX)
app.include_router(
    documents_router,
    prefix=settings.API_PREFIX,
    dependencies=[Depends(auth_dependency)],
)
app.include_router(
    query_router, prefix=settings.API_PREFIX, dependencies=[Depends(auth_dependency)]
)
app.include_router(
    search_router, prefix=settings.API_PREFIX, dependencies=[Depends(auth_dependency)]
)
app.include_router(
    document_router, prefix=settings.API_PREFIX, dependencies=[Depends(auth_dependency)]
)


if __name__ == "__main__":
    port = int(os.getenv("API_PORT", 8000))
    host = os.getenv("HOST", "127.0.0.1")  # Default to localhost instead of 0.0.0.0

    log.info("Starting API server", host=host, port=port)
    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=True,
        reload_exclude=[".venv/*"],
        timeout_keep_alive=30,  # Reduce keep-alive timeout
        timeout_graceful_shutdown=10,  # Add graceful shutdown timeout
    )
