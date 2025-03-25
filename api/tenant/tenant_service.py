import json
import logging
import os
import secrets
import shutil
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ..auth.models import Tenant, TenantCreate, User, UserCreate
from ..db.tenant_repository import TenantRepository
from ..db.user_repository import UserRepository
from ..utils.storage import GCPStorage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TenantService:
    """Service to manage tenant operations"""

    def __init__(self):
        self.tenant_repo = TenantRepository()
        self.user_repo = UserRepository()
        self.root_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../..")
        )
        self.tenants_dir = os.path.join(self.root_dir, "tenants")
        self.credentials_dir = os.path.join(self.root_dir, "credentials")

        # Ensure directories exist
        os.makedirs(self.tenants_dir, exist_ok=True)
        os.makedirs(self.credentials_dir, exist_ok=True)

    def get_tenant_dir(self, tenant_id: str) -> str:
        """Get the directory path for a tenant."""
        return os.path.join(self.tenants_dir, tenant_id)

    def get_tenant_docs_dir(self, tenant_id: str) -> str:
        """Get the documents directory path for a tenant."""
        return os.path.join(self.get_tenant_dir(tenant_id), "docs")

    def get_tenant_env_file(self, tenant_id: str) -> str:
        """Get the environment file path for a tenant."""
        return os.path.join(self.get_tenant_dir(tenant_id), ".env")

    def tenant_exists(self, tenant_id: str) -> bool:
        """Check if a tenant with the given ID exists."""
        tenant_dir = self.get_tenant_dir(tenant_id)
        env_file = self.get_tenant_env_file(tenant_id)
        return os.path.isdir(tenant_dir) and os.path.isfile(env_file)

    def get_all_tenants(self) -> List[Dict]:
        """Get information for all tenants."""
        tenants = []

        # Scan the tenants directory
        for item in os.listdir(self.tenants_dir):
            tenant_dir = os.path.join(self.tenants_dir, item)
            env_file = os.path.join(tenant_dir, ".env")

            # Check if this is a valid tenant directory with an env file
            if os.path.isdir(tenant_dir) and os.path.isfile(env_file):
                # Parse env file for tenant info
                tenant_info = self._parse_env_file(env_file)
                tenant_info["id"] = item
                tenants.append(tenant_info)

        return tenants

    def _parse_env_file(self, env_file: str) -> Dict:
        """Parse a tenant environment file for tenant information."""
        tenant_info = {
            "name": "Unknown",
            "admin_email": "",
            "created_at": "",
            "status": "active"
        }

        try:
            with open(env_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue

                    if "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip()

                        if key == "TENANT_NAME":
                            tenant_info["name"] = value
                        elif key == "ADMIN_EMAIL":
                            tenant_info["admin_email"] = value
                        elif key == "CREATED_AT":
                            tenant_info["created_at"] = value
                        elif key == "STATUS":
                            tenant_info["status"] = value
        except Exception as e:
            logger.error(f"Error parsing tenant env file {env_file}: {e}")

        return tenant_info

    def create_tenant(self, name: str, admin_email: str, description: str = "") -> str:
        """Create a new tenant with the given information."""
        # Generate a tenant ID - use a secure random token instead of uuid
        tenant_id = secrets.token_hex(8)

        # Create tenant directory
        tenant_dir = self.get_tenant_dir(tenant_id)
        docs_dir = self.get_tenant_docs_dir(tenant_id)

        os.makedirs(tenant_dir, exist_ok=True)
        os.makedirs(docs_dir, exist_ok=True)

        # Create tenant env file
        env_file = self.get_tenant_env_file(tenant_id)
        with open(env_file, "w") as f:
            f.write(f"TENANT_ID={tenant_id}\n")
            f.write(f"TENANT_NAME={name}\n")
            f.write(f"ADMIN_EMAIL={admin_email}\n")
            f.write(f"DESCRIPTION={description}\n")
            f.write(f"CREATED_AT={datetime.now().isoformat()}\n")
            f.write(f"STATUS=active\n")

            # Add GCP credentials if available
            gcp_creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
            if gcp_creds:
                f.write(f"GCP_CREDENTIALS={gcp_creds}\n")

            # Add Docker ports
            f.write(f"API_PORT=8000\n")
            f.write(f"FRONTEND_PORT=3000\n")

        logger.info(f"Created new tenant: {name} (ID: {tenant_id})")
        return tenant_id

    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID"""
        return self.tenant_repo.get_tenant(tenant_id)

    def list_tenants(self) -> List[Tenant]:
        """List all tenants"""
        return self.tenant_repo.list_tenants()

    def update_tenant(self, tenant_id: str, tenant_data: dict) -> Optional[Tenant]:
        """Update tenant information"""
        tenant = self.tenant_repo.get_tenant(tenant_id)
        if not tenant:
            return None

        # Update fields
        for key, value in tenant_data.items():
            if hasattr(tenant, key):
                setattr(tenant, key, value)

        tenant.updated_at = datetime.now()

        return self.tenant_repo.update_tenant(tenant)

    def delete_tenant(self, tenant_id: str) -> bool:
        """Delete a tenant and all associated data"""
        if not self.tenant_exists(tenant_id):
            logger.error(f"Cannot delete non-existent tenant: {tenant_id}")
            return False

        try:
            # Stop and remove tenant container if running
            try:
                env_vars = {"TENANT_ID": tenant_id}
                cmd = ["docker-compose", "-f", os.path.join(self.root_dir, "shared", "docker-compose.yml"), "down"]

                # Set environment for subprocess
                subprocess_env = os.environ.copy()
                for key, value in env_vars.items():
                    subprocess_env[key] = value

                # Run docker-compose to stop the tenant
                subprocess.run(
                    cmd,
                    env=subprocess_env,
                    check=True,
                    text=True,
                    capture_output=True
                )
            except Exception as e:
                logger.warning(f"Error stopping tenant container for {tenant_id}: {e}")

            # Delete tenant directory
            tenant_dir = self.get_tenant_dir(tenant_id)
            shutil.rmtree(tenant_dir)

            logger.info(f"Deleted tenant: {tenant_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting tenant {tenant_id}: {e}")
            return False

    def _initialize_tenant_infrastructure(self, tenant_id: str):
        """Initialize infrastructure for a new tenant"""
        try:
            # Create tenant GCP folders
            storage = GCPStorage(tenant_id)

            # Create tenant ChromaDB collection directory
            os.makedirs(f"cache/chroma/{tenant_id}", exist_ok=True)

            # Create tenant document processing directory
            os.makedirs(f"cache/documents/{tenant_id}", exist_ok=True)

            # Create tenant config directory in project root
            tenant_dir = os.path.join(self.root_dir, "tenants", tenant_id)
            os.makedirs(tenant_dir, exist_ok=True)

            # Initialize tenant database with default schemas
            # This would depend on your specific DB implementation

            logger.info(f"Initialized infrastructure for tenant {tenant_id}")
            return True
        except Exception as e:
            logger.error(f"Error initializing tenant infrastructure: {e}")
            return False

    def _cleanup_tenant_infrastructure(self, tenant_id: str):
        """Clean up infrastructure for a deleted tenant"""
        try:
            # Clean up local ChromaDB collection
            chroma_dir = f"cache/chroma/{tenant_id}"
            if os.path.exists(chroma_dir):
                shutil.rmtree(chroma_dir)

            # Clean up document processing directory
            docs_dir = f"cache/documents/{tenant_id}"
            if os.path.exists(docs_dir):
                shutil.rmtree(docs_dir)

            # Clean up tenant config directory in project root
            tenant_dir = os.path.join(self.root_dir, "tenants", tenant_id)
            if os.path.exists(tenant_dir):
                shutil.rmtree(tenant_dir)

            # Note: We're not automatically deleting GCP storage as it may
            # be needed for compliance/backup reasons

            logger.info(f"Cleaned up infrastructure for tenant {tenant_id}")
            return True
        except Exception as e:
            logger.error(f"Error cleaning up tenant infrastructure: {e}")
            return False

    def _generate_temp_password(self, length=12):
        """Generate a temporary password for admin users"""
        import random
        import string

        chars = string.ascii_letters + string.digits + "!@#$%^&*()"
        return "".join(random.choice(chars) for _ in range(length))

    def provision_tenant_container(self, tenant_id: str) -> bool:
        """Provision a Docker container for the tenant."""
        if not self.tenant_exists(tenant_id):
            logger.error(f"Cannot provision container for non-existent tenant: {tenant_id}")
            return False

        try:
            # Set up environment variables
            env_vars = {
                "TENANT_ID": tenant_id,
                "API_PORT": "8000",  # These will be mapped differently for each tenant
                "FRONTEND_PORT": "3000"
            }

            # Get GCP credentials
            gcp_credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")

            # If credentials don't exist, create a placeholder
            if not gcp_credentials_path or not os.path.exists(gcp_credentials_path):
                # Create placeholder file
                placeholder_path = os.path.join(self.credentials_dir, "placeholder.json")
                with open(placeholder_path, "w") as f:
                    f.write("{}")
                gcp_credentials_path = placeholder_path

            # Add to environment variables
            env_vars["GCP_CREDENTIALS"] = gcp_credentials_path

            # Build command safely - don't execute user input directly
            cmd = ["docker-compose", "-f", os.path.join(self.root_dir, "shared", "docker-compose.yml"), "up", "-d"]

            # Set environment for subprocess
            subprocess_env = os.environ.copy()
            for key, value in env_vars.items():
                subprocess_env[key] = value

            # Run docker-compose to start the tenant
            result = subprocess.run(
                cmd,
                env=subprocess_env,
                check=True,
                text=True,
                capture_output=True
            )

            logger.info(f"Provisioned container for tenant {tenant_id}: {result.stdout}")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"Error provisioning container for tenant {tenant_id}: {e}")
            logger.error(f"Command output: {e.stdout}")
            logger.error(f"Command error: {e.stderr}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error provisioning container for tenant {tenant_id}: {e}")
            return False

    def _get_available_port(self, start_port=8100):
        """Find an available port for the new tenant container"""
        import socket

        current_port = start_port
        while current_port < 9000:  # Upper limit for port search
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(("127.0.0.1", current_port))
            sock.close()

            if result != 0:  # Port is available
                return current_port

            current_port += 1

        raise Exception("No available ports found")
