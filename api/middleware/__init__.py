"""Middleware modules for the Legal Search RAG system."""

# Import middleware components
from middleware.cost_control import CostControlMiddleware

__all__ = [
    "CostControlMiddleware",
]
