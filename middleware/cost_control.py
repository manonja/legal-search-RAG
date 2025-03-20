"""Cost control middleware for OpenAI API calls."""

import logging
from typing import Callable, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from utils.token_counter import estimate_tokens_and_cost, format_cost
from utils.usage_db import check_quota_exceeded, get_quota_info

logger = logging.getLogger(__name__)


class CostControlMiddleware(BaseHTTPMiddleware):
    """Middleware for controlling OpenAI API costs."""

    def __init__(self, app: FastAPI, exclude_paths: Optional[List[str]] = None):
        """Initialize middleware.

        Args:
            app: FastAPI application
            exclude_paths: List of paths to exclude from cost control
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/admin",
        ]
        logger.info("Cost control middleware initialized")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and apply cost controls.

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

        # Only apply to POST requests to /rag-search
        if request.method == "POST" and path == "/rag-search":
            # Check if quota is exceeded
            exceeded, reason = check_quota_exceeded()
            if exceeded:
                logger.warning(f"Request blocked: {reason}")
                return Response(
                    content=f'{{"error": "API quota exceeded. {reason}"}}',
                    status_code=429,
                    media_type="application/json",
                )

            # Perform pre-request cost estimate if body contains OpenAI params
            try:
                # Clone the request to read the body
                body = await request.json()

                # Check if this is an OpenAI request with messages
                if body.get("messages"):
                    # Estimate cost
                    estimate = estimate_tokens_and_cost(
                        body.get("messages", []),
                        body.get("model", "gpt-3.5-turbo"),
                        body.get("max_tokens", 500),
                    )

                    # Get warning threshold
                    quota = get_quota_info()
                    threshold = quota.get("cost_warning_threshold", 0.10)

                    # Log the estimate
                    formatted_cost = format_cost(estimate["cost"])
                    logger.info(
                        f"Estimated cost: {formatted_cost} for request to {path}"
                    )

                    # Check against threshold
                    if estimate["cost"] > threshold:
                        logger.warning(
                            f"High cost request detected: {formatted_cost} "
                            f"exceeds threshold of ${threshold}"
                        )
                        # We don't block but add a header to indicate high cost
                        response = await call_next(request)
                        response.headers["X-Cost-Warning"] = (
                            f"Estimated cost {formatted_cost} "
                            f"exceeds threshold ${threshold}"
                        )
                        return response
            except Exception as e:
                # Log error but don't block the request
                logger.error(f"Error in cost estimation: {e}")

        # Process the request normally
        return await call_next(request)


def enforce_quota(request: Dict) -> None:
    """Enforce API usage quota.

    Args:
        request: Request data

    Raises:
        HTTPException: If quota is exceeded
    """
    exceeded, reason = check_quota_exceeded()
    if exceeded:
        logger.warning(f"Request blocked due to quota: {reason}")
        raise HTTPException(status_code=429, detail=f"API quota exceeded. {reason}")


def cost_warning(
    messages: List[Dict[str, str]], model: str = "gpt-3.5-turbo", max_tokens: int = 500
) -> Optional[str]:
    """Generate a cost warning if estimated cost exceeds threshold.

    Args:
        messages: List of message dictionaries
        model: Model to use for completion
        max_tokens: Maximum tokens for completion

    Returns:
        Warning message if cost exceeds threshold, None otherwise
    """
    estimate = estimate_tokens_and_cost(messages, model, max_tokens)
    quota = get_quota_info()
    threshold = quota.get("cost_warning_threshold", 0.10)

    formatted_cost = format_cost(estimate["cost"])

    if estimate["cost"] > threshold:
        warning = (
            f"⚠️ High cost operation: {formatted_cost} "
            f"({estimate['total_tokens']} tokens) "
            f"exceeds threshold of ${threshold:.2f}"
        )
        logger.warning(warning)
        return warning

    return None
