import logging
import os
from typing import Callable, Optional

from dotenv import load_dotenv
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from jose import JWTError, jwt

# Load environment variables
load_dotenv()

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = "HS256"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TenantMiddleware:
    """Middleware to enforce tenant isolation"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, request: Request, call_next):
        try:
            # Extract tenant ID from request
            tenant_id = self._get_tenant_id(request)

            # Set tenant context
            request.state.tenant_id = tenant_id

            # Process the request
            response = await call_next(request)
            return response

        except HTTPException as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail}
            )
        except Exception as e:
            logger.error(f"Unexpected error in tenant middleware: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Internal server error"}
            )

    def _get_tenant_id(self, request: Request) -> str:
        """Extract tenant ID from request"""

        # Try to get tenant ID from path parameter
        path_tenant = self._get_path_tenant(request)
        if path_tenant:
            return path_tenant

        # Try to get tenant ID from Authorization header
        auth_tenant = self._get_auth_tenant(request)
        if auth_tenant:
            return auth_tenant

        # Try to get tenant ID from query parameter
        query_tenant = self._get_query_tenant(request)
        if query_tenant:
            return query_tenant

        # Default to environment variable for tenant ID
        # This is for scenarios where the API is deployed in tenant-specific containers
        env_tenant = os.getenv("TENANT_ID", "default")

        # For public routes (login, etc), we'll use the default tenant
        if self._is_public_route(request.url.path):
            return env_tenant

        # Return the default tenant (container-specific)
        return env_tenant

    def _get_path_tenant(self, request: Request) -> Optional[str]:
        """Get tenant ID from path parameter"""
        try:
            # Check if route has a tenant ID path parameter
            if request.path_params and "tenant_id" in request.path_params:
                return request.path_params["tenant_id"]
        except:
            pass
        return None

    def _get_query_tenant(self, request: Request) -> Optional[str]:
        """Get tenant ID from query parameter"""
        try:
            # Check if there's a tenant ID query parameter
            tenant_id = request.query_params.get("tenant_id")
            if tenant_id:
                return tenant_id
        except:
            pass
        return None

    def _get_auth_tenant(self, request: Request) -> Optional[str]:
        """Get tenant ID from JWT token in Authorization header"""
        try:
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return None

            token = auth_header.replace("Bearer ", "")
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

            # Extract tenant ID from token
            tenant_id = payload.get("tenant_id")
            return tenant_id
        except JWTError:
            return None
        except:
            return None

    def _is_public_route(self, path: str) -> bool:
        """Check if the route is a public route that doesn't require tenant isolation"""
        public_routes = [
            "/auth/token",
            "/auth/register",
            "/docs",
            "/openapi.json",
            "/api/health"
        ]

        for route in public_routes:
            if path.startswith(route):
                return True

        return False
