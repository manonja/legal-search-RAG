"""Configuration management for the application.

This module provides settings and configuration management for the application.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings.

    This class manages all application settings and configuration.
    """

    # API Settings
    API_TITLE: str = "Legal Document RAG API"
    API_DESCRIPTION: str = "API for legal document retrieval and question answering"
    API_VERSION: str = "1.0.0"
    API_PREFIX: str = "/api"
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000

    # File Storage Settings
    DATA_DIR: Path = Path("data")
    CHROMA_DIR: Path = Path("data/chroma")
    CHUNKS_DIR: Path = Path("data/chunks")
    DATA_ROOT: str = "~/legal-search-data"
    INPUT_DIR: str = "~/legal-search-data/input"
    OUTPUT_DIR: str = "~/legal-search-data/processed"
    CHROMA_DATA_DIR: str = "~/legal-search-data/chroma"

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
    GCP_PROJECT_ID: str = "legal-search"
    GCS_BUCKET_NAME: str = "justice-legal-docs"

    # JWT Settings
    JWT_SECRET_KEY: str = "$(openssl rand -hex 32)"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Tenant Settings
    TENANT_ID: str = "default"
    TENANT_ROOT: str = "/app/tenants/default"
    CACHE_DIR: str = "/app/tenants/default/cache"
    MAX_TENANTS: int = 100

    # Rate Limiting
    RATE_LIMIT_TOKENS: int = 100
    RATE_LIMIT_REFILL_TIME: int = 60

    # Other Settings
    HOST: str = "127.0.0.1"
    FRONTEND_PORT: int = 3000
    HTTP_PORT: int = 80
    HTTPS_PORT: int = 443
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False
    ADMIN_API_KEY: str = "your_admin_api_key_here"
    SENTRY_DSN: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="allow",  # Allow extra fields from env file
    )


def get_settings() -> Settings:
    """Get application settings.

    Returns:
        Settings instance with current configuration
    """
    return Settings()
