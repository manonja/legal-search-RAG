"""Google Cloud Storage utilities for document storage.

This module provides functionality to interact with Google Cloud Storage
for storing and retrieving legal documents.
"""

import logging
import os
from typing import List, Optional, Tuple

from google.cloud import storage
from google.cloud.exceptions import GoogleCloudError

from utils.env import get_gcp_config, get_tenant_id, is_gcp_configured

logger = logging.getLogger(__name__)


def init_storage_client() -> Optional[storage.Client]:
    """Initialize Google Cloud Storage client.

    Returns:
        storage.Client: Initialized GCP storage client or None if not configured
    """
    if not is_gcp_configured():
        logger.warning("GCP storage is not properly configured")
        return None

    config = get_gcp_config()
    try:
        # If GOOGLE_APPLICATION_CREDENTIALS is set as env var,
        # the client will use it automatically
        client = storage.Client(project=config["project_id"])
        logger.info(
            f"GCP storage client initialized for project: {config['project_id']}"
        )
        return client
    except Exception as e:
        logger.error(f"Failed to initialize GCP storage client: {e}")
        return None


def get_bucket_name() -> str:
    """Get the GCS bucket name with optional tenant prefix.

    Returns:
        str: GCS bucket name to use for storage
    """
    config = get_gcp_config()
    if config is None:
        return ""

    bucket_name = config["bucket_name"]
    tenant_id = get_tenant_id()

    # If we're using multi-tenant setup, we can optionally prefix folder paths with tenant ID
    # The actual bucket name remains the same
    return bucket_name


def upload_file(local_path: str, gcs_path: Optional[str] = None) -> Tuple[bool, str]:
    """Upload a file to Google Cloud Storage.

    Args:
        local_path: Path to the local file
        gcs_path: Destination path in GCS (optional, if not provided will use filename)

    Returns:
        Tuple[bool, str]: Success status and public URL or error message
    """
    config = get_gcp_config()
    if not config:
        return False, "GCP not configured"

    try:
        storage_client = storage.Client(project=config["project_id"])
        bucket = storage_client.bucket(config["bucket_name"])
        blob = bucket.blob(gcs_path)
        blob.upload_from_filename(local_path)

        return True, f"gs://{config['bucket_name']}/{gcs_path}"
    except Exception as e:
        logger.error(f"Error uploading to GCS: {str(e)}")
        return False, str(e)


def download_file(gcs_path: str, local_path: str) -> Tuple[bool, str]:
    """Download a file from Google Cloud Storage.

    Args:
        gcs_path: Source path in GCS
        local_path: Destination path for local file

    Returns:
        Tuple[bool, str]: Success status and local file path or error message
    """
    client = init_storage_client()
    if client is None:
        return False, "GCP storage client not initialized"

    bucket_name = get_bucket_name()
    if not bucket_name:
        return False, "GCP bucket name is not configured"

    # Prefix with tenant ID for multi-tenant setups
    tenant_id = get_tenant_id()
    gcs_path = f"{tenant_id}/{gcs_path}"

    try:
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(gcs_path)

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(local_path), exist_ok=True)

        # Download the file
        blob.download_to_filename(local_path)

        logger.info(f"Downloaded gs://{bucket_name}/{gcs_path} to {local_path}")
        return True, local_path
    except GoogleCloudError as e:
        error_msg = f"GCP storage error: {str(e)}"
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Error downloading from GCP: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def list_files(prefix: Optional[str] = None) -> List[str]:
    """List files in the GCS bucket with optional prefix.

    Args:
        prefix: Optional prefix to filter files by

    Returns:
        List[str]: List of file paths in the bucket
    """
    client = init_storage_client()
    if client is None:
        logger.warning("GCP storage client not initialized")
        return []

    bucket_name = get_bucket_name()
    if not bucket_name:
        logger.warning("GCP bucket name is not configured")
        return []

    # Set up prefix with tenant ID
    tenant_id = get_tenant_id()
    if prefix:
        full_prefix = f"{tenant_id}/{prefix}"
    else:
        full_prefix = f"{tenant_id}/"

    try:
        bucket = client.bucket(bucket_name)
        blobs = list(bucket.list_blobs(prefix=full_prefix))

        # Return just the filenames without the tenant prefix
        prefix_len = len(full_prefix)
        return [blob.name[prefix_len:] for blob in blobs]
    except GoogleCloudError as e:
        logger.error(f"GCP storage error: {str(e)}")
        return []
    except Exception as e:
        logger.error(f"Error listing files from GCP: {str(e)}")
        return []


def file_exists(gcs_path: str) -> bool:
    """Check if a file exists in Google Cloud Storage.

    Args:
        gcs_path: Path to check in GCS

    Returns:
        bool: True if file exists, False otherwise
    """
    client = init_storage_client()
    if client is None:
        return False

    bucket_name = get_bucket_name()
    if not bucket_name:
        return False

    # Prefix with tenant ID for multi-tenant setups
    tenant_id = get_tenant_id()
    gcs_path = f"{tenant_id}/{gcs_path}"

    try:
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(gcs_path)
        return blob.exists()
    except Exception as e:
        logger.error(f"Error checking file existence in GCP: {str(e)}")
        return False


def get_file_content(gcs_path: str) -> Tuple[bool, Optional[str]]:
    """Get the content of a file from Google Cloud Storage.

    Args:
        gcs_path: Path to the file in GCS

    Returns:
        Tuple[bool, Optional[str]]: Success status and file content or None
    """
    client = init_storage_client()
    if client is None:
        return False, None

    bucket_name = get_bucket_name()
    if not bucket_name:
        return False, None

    # Prefix with tenant ID for multi-tenant setups
    tenant_id = get_tenant_id()
    gcs_path = f"{tenant_id}/{gcs_path}"

    try:
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(gcs_path)

        if not blob.exists():
            return False, None

        # Download content to memory
        content = blob.download_as_text()
        return True, content
    except Exception as e:
        logger.error(f"Error getting file content from GCP: {str(e)}")
        return False, None
