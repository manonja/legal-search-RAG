"""Startup service for application initialization.

This module provides functionality for initializing application components
on startup.
"""

import os
import sentry_sdk
from pathlib import Path
from app.core.struct_logger import log

from app.core.config import get_settings
from app.services.database.init_db import init_vector_db


async def initialize_application():
    """Initialize application components on startup.

    This function:
    1. Creates necessary directories
    2. Initializes pgvector database
    3. Sets up other application components

    Raises:
        Exception: If initialization fails
    """
    try:
        # Get settings
        settings = get_settings()

        # Create necessary directories
        settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
        log.info(
            "Created necessary directories",
            data_dir=str(settings.DATA_DIR),
        )

        # Initialize pgvector database
        try:
            init_vector_db()
            log.info("Successfully initialized pgvector database")
        except Exception as db_error:
            log.error("Error initializing pgvector database", error=str(db_error))
            sentry_sdk.capture_exception(db_error)
            # Continue startup even if database initialization fails
            # This allows the application to start even with DB issues

        log.info("Application initialization completed successfully")

    except Exception as e:
        log.error("Error during application initialization", error=str(e))
        # Capture startup errors in Sentry
        sentry_sdk.capture_exception(e)
        raise
