"""Startup service for application initialization.

This module provides functionality for initializing application components
on startup.
"""

import logging
import os
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from sentry_sdk.integrations.threading import ThreadingIntegration

from pathlib import Path

from app.core.config import get_settings
from app.services.database.chroma import initialize_chroma_collection

logger = logging.getLogger(__name__)


def initialize_sentry():
    """Initialize Sentry for error tracking.

    Configures Sentry SDK based on environment variables and settings.
    Only enables Sentry in production or if explicitly configured.
    """
    settings = get_settings()

    # Only initialize Sentry if not in test mode and DSN is provided
    if not os.getenv("TESTING") == "true" and settings.SENTRY_DSN:
        logger.info("Initializing Sentry")
        # Configure Sentry integrations
        logging_integration = LoggingIntegration(
            level=logging.INFO,  # Capture info and above as breadcrumbs
            event_level=logging.ERROR,  # Send errors as events
        )

        # Set up all integrations for comprehensive error tracking
        integrations = [
            # Core FastAPI integration
            FastApiIntegration(),
            # Log all error events
            logging_integration,
            # Track async errors
            AsyncioIntegration(),
            # Track threading errors
            ThreadingIntegration(propagate_hub=True),
        ]

        # Initialize Sentry with all integrations
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            integrations=integrations,
            # Enable performance monitoring
            enable_tracing=settings.SENTRY_ENABLE_TRACING,
            # Configure environment
            environment=settings.SENTRY_ENVIRONMENT,
            # Set traces sample rate (adjust based on traffic volume)
            traces_sample_rate=settings.sentry_traces_sample_rate,
            # Set profiles sample rate for performance profiling
            profiles_sample_rate=settings.SENTRY_PROFILES_SAMPLE_RATE,
            # Add debug flag for development
            debug=settings.DEBUG,
            # Add user identification data for better error tracking
            send_default_pii=settings.SENTRY_SEND_PII,
            # Ensure all unhandled exceptions are captured, including in production
            auto_enabling_integrations=False,
            attach_stacktrace=True,
            before_send=before_send_handler,
        )

        # Add a global tag for easier filtering in Sentry
        sentry_sdk.set_tag("app_name", "legal-search-rag-api")

        logger.info(
            f"Sentry initialized for environment: {settings.SENTRY_ENVIRONMENT}"
        )

        # In production, just log initialization without test events
        if settings.is_production:
            logger.info("Sentry initialized in production mode")
        # In development/staging, test with an info message
        else:
            sentry_sdk.capture_message(
                "Sentry test message from application startup", level="info"
            )
    else:
        logger.info("Sentry disabled (testing or no DSN configured)")
        # Explicitly disable Sentry with empty DSN to ensure it's not accidentally used
        try:
            sentry_sdk.init(dsn="")
        except Exception as e:
            logger.debug(f"Error while disabling Sentry: {e}")
            # Continue execution - Sentry not being disabled is not critical


def before_send_handler(event, hint):
    """Process events before sending to Sentry.

    This function allows filtering or modifying events before they are sent to Sentry.

    Args:
        event: The event data dictionary
        hint: A dictionary containing additional information about the event

    Returns:
        Modified event or None to discard the event
    """
    # Check for specific error types we might want to filter
    if "exc_info" in hint:
        exc_type, exc_value, tb = hint["exc_info"]

        # Example: filter out specific exceptions you don't want to track
        # if isinstance(exc_value, ConnectionRefusedError):
        #    return None  # Don't send connection errors to Sentry

    # Add additional context to all events
    if event.get("request", {}).get("url", "").startswith("/api/health"):
        # Don't send health check endpoints to reduce noise
        return None

    return event


async def initialize_application():
    """Initialize application components on startup.

    This function:
    1. Creates necessary directories
    2. Initializes Sentry for error monitoring
    3. Initializes ChromaDB collection
    4. Sets up other application components

    Raises:
        Exception: If initialization fails
    """
    try:
        # Get settings
        settings = get_settings()

        # Create necessary directories
        settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
        settings.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("Created necessary directories")

        # Initialize Sentry for error tracking
        initialize_sentry()

        # Initialize ChromaDB collection
        await initialize_chroma_collection()

        logger.info("Application initialization completed successfully")

    except Exception as e:
        logger.error(f"Error during application initialization: {e}")
        # Capture startup errors in Sentry if already initialized
        sentry_sdk.capture_exception(e)
        raise
