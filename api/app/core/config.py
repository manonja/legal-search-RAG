"""Configuration management for the application.

This module provides settings and configuration management for the application.
"""

import logging
import os
import tempfile
from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)

# Required environment variables
REQUIRED_ENV_VARS = ["GOOGLE_API_KEY", "OPENAI_API_KEY"]


class Settings(BaseSettings):
    """Application settings.

    This class manages all application settings and configuration.
    """

    # API Settings
    API_TITLE: str = "Legal Document RAG API"
    API_DESCRIPTION: str = "API for legal document retrieval and question answering"
    API_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    API_TOKEN: Optional[str] = None

    # File Storage Settings
    _temp_dir: str = tempfile.mkdtemp(prefix="legal-search-")
    DATA_DIR: Path = os.path.join(_temp_dir, "data")
    CHROMA_DIR: Path = os.path.join(_temp_dir, "chroma")

    # OpenAI Settings
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    EMBEDDING_MODEL: str = "text-embedding-ada-002"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    # ChromaDB Settings
    COLLECTION_NAME: str = "legal_docs"

    # Google Settings
    GOOGLE_API_KEY: Optional[str] = None
    GOOGLE_MODEL: str = "gemini-pro"
    USE_GCP_STORAGE: bool = False
    GCP_PROJECT_ID: str = "952577461734"
    GCS_BUCKET_NAME: str = "justice-legal-docs"
    GCP_SECRET_NAME: str = "maja-legal-api-token"  # noqa: S105
    GCP_SECRET_VERSION: str = "1"  # noqa: S105

    # Other Settings
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False
    SENTRY_DSN: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="allow",  # Allow extra fields from env file
    )

    def get_google_api_key(self) -> str:
        """Get the Google API key.

        Returns:
            str: The Google API key.

        Raises:
            ValueError: If GOOGLE_API_KEY is not set.
        """
        if not self.GOOGLE_API_KEY:
            raise ValueError(
                "GOOGLE_API_KEY environment variable is not set. "
                "Please copy .env.example to .env and set your API key."
            )
        return self.GOOGLE_API_KEY


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get application settings.

    Returns:
        Settings instance with current configuration
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
