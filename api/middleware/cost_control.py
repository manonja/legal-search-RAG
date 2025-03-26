"""Cost control middleware for OpenAI API calls."""

import logging
import os
from typing import Callable, Dict, List, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class CostControlMiddleware(BaseHTTPMiddleware):
    """Middleware for logging and monitoring API requests."""

    def __init__(self, app):
        """Initialize middleware.

        Args:
            app: FastAPI application
        """
        super().__init__(app)
        self.exclude_paths = ["/docs", "/redoc", "/openapi.json"]
        logger.info("Cost control middleware initialized")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and log activity.

        Args:
            request: FastAPI request object
            call_next: Next middleware in chain

        Returns:
            FastAPI response
        """
        # Skip checks for excluded paths
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.exclude_paths):
            return await call_next(request)

        # Log API request
        if request.method == "POST" and path in ["/search", "/rag-search"]:
            logger.info(f"Processing request to {path}")

            # Add warning header for expensive operations
            if path == "/rag-search":
                response = await call_next(request)
                response.headers["X-Cost-Warning"] = (
                    "RAG operations use tokens from your OpenAI account"
                )
                return response

        # Process the request normally
        return await call_next(request)
