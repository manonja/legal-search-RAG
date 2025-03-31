"""Core configuration settings for the application."""

import os
from pathlib import Path

# API settings
API_VERSION = "1.0.0"
API_TITLE = "Legal Document Search API"
API_DESCRIPTION = "API for searching legal documents using semantic similarity"
API_PREFIX = "/api"

# Model settings
EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "legal_docs")

# Cache settings
CACHE_PATH = os.path.join(os.path.dirname(__file__), "../../cache", "query_cache.json")

# API key settings
ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "1234")


# Directory settings
def get_app_dir() -> Path:
    """Get the application directory."""
    return Path(__file__).parent.parent.parent.absolute()
