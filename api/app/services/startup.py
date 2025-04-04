"""Startup service for application initialization.

This module provides functionality for initializing application components
on startup.
"""

import os
import sentry_sdk
from pathlib import Path
from struct_logger import log

from app.core.config import get_settings
from app.services.database.chroma import initialize_chroma_collection


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
        log.info(
            "Created necessary directories",
            data_dir=str(settings.DATA_DIR),
            chroma_dir=str(settings.CHROMA_DIR),
        )

        # Initialize ChromaDB collection
        await initialize_chroma_collection()

        log.info("Application initialization completed successfully")

    except Exception as e:
        log.error("Error during application initialization", error=str(e))
        # Capture startup errors in Sentry
        sentry_sdk.capture_exception(e)
        raise
