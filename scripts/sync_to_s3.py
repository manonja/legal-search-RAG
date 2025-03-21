#!/usr/bin/env python3
"""
Script to synchronize local legal documents to S3 storage.

This script uploads all documents from the local document directories
to the configured S3 bucket, maintaining the directory structure.
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import modules
script_dir = Path(__file__).resolve().parent
parent_dir = script_dir.parent
sys.path.append(str(parent_dir))

from utils.env import get_docs_root, is_s3_configured
from utils.s3_utils import upload_directory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def sync_documents_to_s3(docs_dir, chunks_dir):
    """Upload all documents and chunks to S3.

    Args:
        docs_dir: Path to the documents directory
        chunks_dir: Path to the chunks directory

    Returns:
        Boolean indicating success
    """
    if not is_s3_configured():
        logger.error(
            "S3 not properly configured. Please set the required environment variables."
        )
        return False

    # First upload the full documents
    logger.info(f"Syncing documents from {docs_dir} to S3...")
    doc_results = upload_directory(docs_dir, recursive=True)

    doc_success = sum(1 for success in doc_results.values() if success)
    doc_failure = sum(1 for success in doc_results.values() if not success)

    # Then upload the chunked documents
    logger.info(f"Syncing document chunks from {chunks_dir} to S3...")
    chunk_results = upload_directory(chunks_dir, recursive=True)

    chunk_success = sum(1 for success in chunk_results.values() if success)
    chunk_failure = sum(1 for success in chunk_results.values() if not success)

    # Summary
    logger.info(f"Documents: {doc_success} uploaded, {doc_failure} failed")
    logger.info(f"Chunks: {chunk_success} uploaded, {chunk_failure} failed")

    return (doc_failure + chunk_failure) == 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Sync documents to S3")
    parser.add_argument(
        "--docs-dir",
        help="Path to documents directory",
        default=get_docs_root(),
    )
    parser.add_argument(
        "--chunks-dir",
        help="Path to document chunks directory",
        default=os.path.expanduser("~/Downloads/chunkedLegalDocs"),
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Validate directories
    docs_dir = Path(args.docs_dir)
    chunks_dir = Path(args.chunks_dir)

    if not docs_dir.exists():
        logger.error(f"Documents directory not found: {docs_dir}")
        return 1

    if not chunks_dir.exists():
        logger.error(f"Chunks directory not found: {chunks_dir}")
        return 1

    # Sync to S3
    success = sync_documents_to_s3(docs_dir, chunks_dir)

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
