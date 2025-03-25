#!/usr/bin/env python
"""Test script for Google Cloud Storage integration.

This script verifies that the GCP credentials are properly configured
and that we can upload, download, and list files in the GCS bucket.
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
from utils.gcp_storage import (
    download_file,
    file_exists,
    get_file_content,
    list_files,
    upload_file,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    """Run GCP storage tests."""
    # Load environment variables
    load_dotenv()

    # Check if GCP is configured
    if not is_gcp_configured():
        logger.error("GCP is not properly configured. Check your .env file.")
        return

    # Get GCP configuration
    config = get_gcp_config()
    logger.info(
        f"GCP configuration: project_id={config['project_id']}, bucket={config['bucket_name']}"
    )

    # Test file name
    test_file_name = "gcp_test.txt"
    test_content = "This is a test file for GCP storage integration."

    # Create a temporary file
    with tempfile.NamedTemporaryFile(delete=False, mode="w") as temp:
        temp.write(test_content)
        temp_path = temp.name

    try:
        # Test uploading a file
        logger.info(f"Uploading test file: {temp_path}")
        success, url = upload_file(temp_path, test_file_name)

        if not success:
            logger.error(f"Failed to upload file: {url}")
            return

        logger.info(f"Successfully uploaded file: {url}")

        # Test checking if file exists
        logger.info(f"Checking if {test_file_name} exists")
        if file_exists(test_file_name):
            logger.info(f"File {test_file_name} exists in GCS")
        else:
            logger.error(f"File {test_file_name} doesn't exist in GCS")
            return

        # Test listing files
        logger.info("Listing files in GCS bucket")
        files = list_files()
        logger.info(f"Files in bucket: {files}")

        # Test getting file content
        logger.info(f"Getting content of {test_file_name}")
        success, content = get_file_content(test_file_name)
        if success:
            logger.info(f"File content: {content}")
        else:
            logger.error("Failed to get file content")
            return

        # Test downloading the file
        download_path = str(Path.home() / f"Downloads/{test_file_name}")
        logger.info(f"Downloading {test_file_name} to {download_path}")
        success, local_path = download_file(test_file_name, download_path)

        if success:
            logger.info(f"Successfully downloaded file to {local_path}")
            # Verify content
            with open(local_path, "r") as f:
                downloaded_content = f.read()

            if downloaded_content == test_content:
                logger.info("Downloaded content matches original content")
            else:
                logger.error("Downloaded content doesn't match original content")
        else:
            logger.error(f"Failed to download file: {local_path}")

    finally:
        # Clean up
        os.unlink(temp_path)
        if os.path.exists(str(Path.home() / f"Downloads/{test_file_name}")):
            os.unlink(str(Path.home() / f"Downloads/{test_file_name}"))

        logger.info("Test completed")


if __name__ == "__main__":
    main()
