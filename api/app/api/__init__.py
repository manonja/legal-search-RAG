"""API router initialization."""

from fastapi import APIRouter

from app.api.endpoints.admin import router as admin_router

# Create API router
api_router = APIRouter()

# Include routers from endpoints
api_router.include_router(admin_router)

# Add more endpoint routers as needed
