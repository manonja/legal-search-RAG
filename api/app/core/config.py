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
    DATA_DIR: Path = Path("data")
    CHROMA_DIR: Path = Path("data/chroma")
    _temp_dir: str = tempfile.mkdtemp(prefix="legal-search-")
    DATA_ROOT: str = os.path.join(_temp_dir, "data")
    INPUT_DIR: str = os.path.join(_temp_dir, "input")
    OUTPUT_DIR: str = os.path.join(_temp_dir, "processed")
    CHROMA_DATA_DIR: str = os.path.join(_temp_dir, "chroma")
    DOCS_ROOT: str = os.path.join(_temp_dir, "docs")
    CHUNKS_ROOT: str = os.path.join(_temp_dir, "chunks")

    # OpenAI Settings
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    EMBEDDING_MODEL: str = "text-embedding-ada-002"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_MONTHLY_BUDGET: float = 30.0
    MAX_QUERIES_PER_MONTH: int = 100
    ENABLE_COST_WARNINGS: bool = True
    MAX_MONTHLY_COST: float = 50.0
    MAX_EMBEDDING_TOKENS: int = 1000000

    # ChromaDB Settings
    COLLECTION_NAME: str = "legal_docs"
    CHROMA_HOST: str = "127.0.0.1"
    CHROMA_PORT: int = 8000

    # Google Settings
    GOOGLE_API_KEY: Optional[str] = None
    GOOGLE_MODEL: str = "gemini-pro"
    USE_GCP_STORAGE: bool = False
    GCP_PROJECT_ID: str = "952577461734"
    GCS_BUCKET_NAME: str = "justice-legal-docs"
    GCP_SECRET_NAME: str = "maja-legal-api-token"  # noqa: S105
    GCP_SECRET_VERSION: str = "1"  # noqa: S105

    # Other Settings
    HOST: str = "127.0.0.1"
    FRONTEND_PORT: int = 3000
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False
    ADMIN_API_KEY: str = "your_admin_api_key_here"
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

    # Path property methods
    @property
    def data_root_path(self) -> Path:
        """Get the data root directory.

        Returns:
            Path: Path to the data root directory
        """
        return Path(self.DATA_ROOT)

    @property
    def input_dir_path(self) -> Path:
        """Get the input directory.

        Returns:
            Path: Path to the input directory
        """
        return Path(self.INPUT_DIR)

    @property
    def output_dir_path(self) -> Path:
        """Get the output directory.

        Returns:
            Path: Path to the output directory
        """
        return Path(self.OUTPUT_DIR)

    @property
    def chroma_dir_path(self) -> Path:
        """Get the ChromaDB directory.

        Returns:
            Path: Path to the ChromaDB directory
        """
        return Path(self.CHROMA_DATA_DIR)

    @property
    def docs_root_path(self) -> Path:
        """Get the path to the documents root directory.

        Returns:
            Path: The path to the documents root directory
        """
        return Path(self.DOCS_ROOT)

    def ensure_directories(self) -> None:
        """Ensure all required directories exist.

        Creates any missing directories that are required for the application to function.
        """
        directories = [
            self.data_root_path,
            self.input_dir_path,
            self.output_dir_path,
            self.chroma_dir_path,
            self.docs_root_path,
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory}")


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
