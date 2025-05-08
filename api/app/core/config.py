"""Configuration management for the application.

This module provides settings and configuration management for the application.
"""

import os
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.struct_logger import log

# Required environment variables
REQUIRED_ENV_VARS = ["GOOGLE_API_KEY", "OPENAI_API_KEY"]

# Read version from VERSION file
ROOT_DIR = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
version_file = ROOT_DIR / "VERSION"
with open(version_file, "r") as f:
    VERSION = f.read().strip()


class Settings(BaseSettings):
    """Application settings.

    This class manages all application settings and configuration.
    """

    # API Settings
    API_TITLE: str = "Legal Document RAG API"
    API_DESCRIPTION: str = "API for legal document retrieval and question answering"
    API_VERSION: str = VERSION
    API_PREFIX: str = "/api"
    API_TOKEN: Optional[str] = None

    # File Storage Settings
    _temp_dir: str = tempfile.mkdtemp(prefix="legal-search-")
    DATA_DIR: Path = Path(os.getenv("DATA_DIR", os.path.join(_temp_dir, "data")))

    # OpenAI Settings
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    EMBEDDING_MODEL: str = "text-embedding-ada-002"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # RunPod Settings
    RUNPOD_API_KEY: Optional[str] = None
    RUNPOD_LLM_URL: str = "https://api.runpod.ai/v2/nlwx0t95z8sw2f"
    RUNPOD_MIXTRAL_ENDPOINT_ID: Optional[str] = None
    RUNPOD_MODEL_NAME: str = "runpod-llm-model"
    RUNPOD_EMBEDDING_ENDPOINT_ID: Optional[str] = None
    HF_EMBEDDING_MODEL: str = "nlpaueb/legal-bert-base-uncased"
    EMBEDDING_DIMENSION: int = 768
    USE_RUNPOD: bool = False

    # Database Settings
    DATABASE_URI: str = Path(os.getenv("DATABASE_URI"))

    # Google Settings
    GOOGLE_API_KEY: Optional[str] = None
    GOOGLE_MODEL: str = "gemini-pro"
    USE_GCP_STORAGE: bool = False
    GCP_PROJECT_ID: str = "952577461734"
    GCS_BUCKET_NAME: str = "justice-legal-docs"

    # Other Settings
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False

    # Sentry Settings
    SENTRY_DSN: Optional[str] = None
    SENTRY_ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    SENTRY_TRACES_SAMPLE_RATE: float = 1
    SENTRY_PROFILES_SAMPLE_RATE: float = 1
    SENTRY_ENABLE_TRACING: bool = True
    SENTRY_SEND_PII: bool = True  # Send personally identifiable information

    # Chunking Settings (New)
    SEMCHUNK_TOKENIZER: str = (
        "cl100k_base"  # Default for text-embedding-3-small/large, gpt-4, gpt-3.5-turbo
    )
    SEMCHUNK_CHUNK_SIZE: int = 512  # Default token chunk size
    SEMCHUNK_OVERLAP_TOKENS: int = 50  # Default token overlap

    # Additional Sentry settings for production
    @property
    def is_production(self) -> bool:
        """Check if the application is running in production environment.

        Returns:
            bool: True if in production environment, False otherwise.
        """
        return self.SENTRY_ENVIRONMENT.lower() == "production"

    @property
    def sentry_traces_sample_rate(self) -> float:
        """Get the appropriate traces sample rate based on environment.

        Returns:
            float: Lower sample rate in production to reduce volume.
        """
        return 0.1 if self.is_production else 0.5

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
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


@lru_cache
def get_settings() -> Settings:
    """Get application settings.

    Returns:
        Settings instance with current configuration
    """
    return Settings()
