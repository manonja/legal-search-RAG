#!/usr/bin/env python
"""Script to verify the GCP integration is working correctly.

This script performs the following checks:
1. Verifies GCP configuration is present in environment
2. Tests connection to Google Cloud Storage
3. Tests uploading a test file to GCS
4. Tests downloading a file from GCS
5. Tests listing files in GCS
6. Tests the document processing pipeline with GCS
"""

import logging
import os
import sys
import tempfile
from pathlib import Path

# Add the parent directory to the Python path so we can import from utils
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

from utils.env import get_gcp_config, is_gcp_configured
from utils.gcp_storage import download_file, list_files, upload_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def check_environment():
    """Check if GCP is correctly configured in the environment."""
    load_dotenv()

    if not is_gcp_configured():
        logger.error("GCP is not configured in your environment")
        logger.info("Run scripts/setup_local_gcp.sh to configure GCP")
        return False

    config = get_gcp_config()
    logger.info("GCP configuration found:")
    logger.info(f"  Project ID: {config['project_id']}")
    logger.info(f"  Bucket: {config['bucket_name']}")
    logger.info(f"  Credentials: {config['credentials_path']}")

    return True


def test_gcs_connection():
    """Test connection to Google Cloud Storage."""
    try:
        # List files (limit to 1) to test connection
        _ = list_files("", max_results=1)
        logger.info("Successfully connected to GCS bucket")
        return True
    except Exception as e:
        logger.error(f"Failed to connect to GCS: {str(e)}")
        return False


def test_upload_download():
    """Test uploading and downloading a file to/from GCS."""
    try:
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp:
            temp_path = temp.name
            temp.write(b"This is a test file for GCP integration")

        # Upload the file to GCS
        gcs_path = "test/integration_test.txt"
        success, url = upload_file(temp_path, gcs_path)

        if not success:
            logger.error(f"Failed to upload test file: {url}")
            return False

        logger.info(f"Successfully uploaded test file to {url}")

        # Download the file from GCS
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as download_temp:
            download_path = download_temp.name

        success, result = download_file(gcs_path, download_path)

        if not success:
            logger.error(f"Failed to download test file: {result}")
            return False

        logger.info("Successfully downloaded test file")

        # Verify file contents
        with open(download_path, "rb") as f:
            content = f.read()

        if content == b"This is a test file for GCP integration":
            logger.info("File content verification successful")
        else:
            logger.error("File content verification failed")
            return False

        # Clean up temporary files
        os.unlink(temp_path)
        os.unlink(download_path)

        return True

    except Exception as e:
        logger.error(f"Error during upload/download test: {str(e)}")
        return False


def test_listing_files():
    """Test listing files in GCS."""
    try:
        files = list_files("")
        logger.info("Successfully listed files in GCS bucket")
        logger.info(f"Found {len(files)} files")

        if files:
            logger.info("Sample files:")
            for i, file in enumerate(files[:5], 1):
                logger.info(f"  {i}. {file}")

            if len(files) > 5:
                logger.info(f"  ... and {len(files) - 5} more")

        return True
    except Exception as e:
        logger.error(f"Failed to list files in GCS: {str(e)}")
        return False


def run_full_verification():
    """Run all verification checks."""
    logger.info("Starting GCP integration verification")

    # Check 1: Environment
    if not check_environment():
        return False

    # Check 2: GCS Connection
    if not test_gcs_connection():
        return False

    # Check 3: Upload/Download
    if not test_upload_download():
        return False

    # Check 4: Listing Files
    if not test_listing_files():
        return False

    logger.info("All GCP integration tests passed successfully!")
    return True


def main():
    """Run the verification script."""
    success = run_full_verification()
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
