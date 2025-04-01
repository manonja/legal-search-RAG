"""API router configuration."""

from fastapi import APIRouter

api_router = APIRouter()

# Import and include other routers here if needed
# Example:
# from app.routers import search, documents
# api_router.include_router(search.router, prefix="/search", tags=["search"])
# api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
