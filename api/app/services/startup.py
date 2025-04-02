"""Startup service for application initialization.

This module provides functionality for initializing application components
on startup.
"""

import logging
import os
import sentry_sdk
from pathlib import Path

from app.core.config import get_settings
from app.services.database.chroma import initialize_chroma_collection

logger = logging.getLogger(__name__)


async def initialize_application():
    """Initialize application components on startup.

    This function:
    1. Creates necessary directories
    2. Initializes ChromaDB collection
    3. Sets up other application components

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

        # Initialize ChromaDB collection
        await initialize_chroma_collection()

        logger.info("Application initialization completed successfully")

    except Exception as e:
        logger.error(f"Error during application initialization: {e}")
        # Capture startup errors in Sentry
        sentry_sdk.capture_exception(e)
        raise
