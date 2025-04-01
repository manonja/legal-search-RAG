"""Configuration settings for the application."""

import os
from pathlib import Path

# API Configuration
API_TITLE = "Legal Search RAG API"
API_DESCRIPTION = "API for legal document search and RAG system"
API_VERSION = "1.0.0"
API_PREFIX = "/api"

# Collection Configuration
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "legal_docs")

# Embedding Model Configuration
EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002")

# Document Processing Configuration
DOCUMENTS_DIR = os.getenv(
    "DOCUMENTS_DIR", os.path.join(os.path.dirname(__file__), "..", "..", "data")
)

# Cache Configuration
CACHE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "cache", "query_cache.json"
)

# Ensure directories exist
os.makedirs(DOCUMENTS_DIR, exist_ok=True)
os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
