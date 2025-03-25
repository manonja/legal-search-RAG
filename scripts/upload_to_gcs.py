#!/usr/bin/env python
"""Script to upload documents to Google Cloud Storage (GCS).

This script allows users to upload document files to the GCS bucket
with the correct structure (input/ prefix) to be used by the document
processing pipeline.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Add the parent directory to the Python path so we can import from utils
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

from utils.env import get_gcp_config, is_gcp_configured
from utils.gcp_storage import list_files, upload_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def upload_document(file_path: str) -> bool:
    """Upload a document to GCS with the input/ prefix.

    Args:
        file_path: Path to the local file to upload

    Returns:
        Boolean indicating if the upload was successful
    """
    if not os.path.isfile(file_path):
        logger.error(f"File does not exist: {file_path}")
        return False

    # Only allow PDF and DOCX files
    if not file_path.lower().endswith((".pdf", ".docx")):
        logger.error(
            f"File type not supported. Only PDF and DOCX files are allowed: {file_path}"
        )
        return False

    # Get just the filename
    filename = os.path.basename(file_path)

    # Upload to GCS with input/ prefix
    gcs_path = f"input/{filename}"
    success, url = upload_file(file_path, gcs_path)

    if success:
        logger.info(f"Successfully uploaded {filename} to {url}")
        return True
    else:
        logger.error(f"Failed to upload {filename}: {url}")
        return False


def list_uploaded_documents():
    """List documents already uploaded to GCS under input/ prefix."""
    files = list_files("input/")

    if not files:
        logger.info("No documents found in the input/ directory")
        return

    logger.info("Documents available in GCS:")
    for i, filename in enumerate(files, 1):
        logger.info(f"{i}. {filename}")


def main():
    """Run the main upload workflow."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Upload documents to Google Cloud Storage"
    )
    parser.add_argument("file", nargs="?", help="Path to the file to upload")
    parser.add_argument(
        "--list", action="store_true", help="List documents already uploaded"
    )
    args = parser.parse_args()

    # Load environment variables
    load_dotenv()

    # Check if GCP is configured
    if not is_gcp_configured():
        logger.error("GCP is not properly configured. Check your .env file.")
        return 1

    config = get_gcp_config()
    logger.info(f"Using GCP bucket: {config['bucket_name']}")

    if args.list:
        list_uploaded_documents()
        return 0

    if not args.file:
        logger.error(
            "Please specify a file to upload or use --list to see uploaded documents"
        )
        return 1

    success = upload_document(args.file)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
