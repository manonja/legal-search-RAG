"""S3 utilities for cloud storage integration."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Union

from utils.env import get_s3_config

logger = logging.getLogger(__name__)


def initialize_s3_client():
    """Initialize and return an S3 client using boto3.

    Returns:
        boto3.client.S3 or None if S3 is not configured or boto3 is not available
    """
    try:
        import boto3

        s3_config = get_s3_config()
        if not s3_config:
            logger.warning("S3 configuration not found")
            return None

        client = boto3.client(
            "s3",
            region_name=s3_config["region"],
            aws_access_key_id=s3_config["access_key"],
            aws_secret_access_key=s3_config["secret_key"],
        )

        logger.info(f"S3 client initialized for bucket {s3_config['bucket']}")
        return client

    except ImportError:
        logger.warning("boto3 not installed. Install with 'pip install boto3'")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize S3 client: {str(e)}")
        return None


def upload_document(
    file_path: Union[str, Path],
    s3_key: Optional[str] = None,
    metadata: Optional[Dict] = None,
) -> bool:
    """Upload a document to S3.

    Args:
        file_path: Path to the local file
        s3_key: Optional custom S3 key, if None will use file name in documents folder
        metadata: Optional metadata to attach to the S3 object

    Returns:
        Boolean indicating if upload was successful
    """
    s3_client = initialize_s3_client()
    if not s3_client:
        return False

    s3_config = get_s3_config()
    if not s3_config:
        return False

    try:
        file_path = Path(file_path)
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return False

        # Determine S3 key if not provided
        if not s3_key:
            s3_key = f"{s3_config['prefix']}/documents/{file_path.name}"

        logger.info(f"Uploading {file_path} to s3://{s3_config['bucket']}/{s3_key}")

        # Set default metadata if none provided
        if metadata is None:
            metadata = {}

        # Upload file
        with open(file_path, "rb") as file_data:
            s3_client.upload_fileobj(
                file_data, s3_config["bucket"], s3_key, ExtraArgs={"Metadata": metadata}
            )

        logger.info(f"Successfully uploaded {file_path.name} to S3")
        return True

    except Exception as e:
        logger.error(f"Failed to upload to S3: {str(e)}")
        return False


def upload_directory(
    dir_path: Union[str, Path], recursive: bool = True
) -> Dict[str, bool]:
    """Upload all files in a directory to S3.

    Args:
        dir_path: Path to local directory
        recursive: Whether to recurse into subdirectories

    Returns:
        Dictionary mapping file paths to upload success/failure
    """
    dir_path = Path(dir_path)
    if not dir_path.is_dir():
        logger.error(f"Not a directory: {dir_path}")
        return {}

    results = {}

    # Get file list based on recursion setting
    if recursive:
        files = list(dir_path.rglob("*"))
    else:
        files = list(dir_path.glob("*"))

    # Filter to only include files (not directories)
    files = [f for f in files if f.is_file()]

    for file_path in files:
        # Create the relative path for the S3 key
        relative_path = file_path.relative_to(dir_path)
        s3_key = f"{get_s3_config()['prefix']}/documents/{relative_path}"

        # Upload the file
        success = upload_document(file_path, s3_key)
        results[str(file_path)] = success

    return results


def check_document_exists(document_id: str) -> bool:
    """Check if a document exists in S3.

    Args:
        document_id: Document identifier (file name)

    Returns:
        Boolean indicating if document exists in S3
    """
    s3_client = initialize_s3_client()
    if not s3_client:
        return False

    s3_config = get_s3_config()
    if not s3_config:
        return False

    try:
        # Try first with standard key
        key = f"{s3_config['prefix']}/documents/{document_id}"
        try:
            s3_client.head_object(Bucket=s3_config["bucket"], Key=key)
            return True
        except:
            # Try with chunked prefix
            key = f"{s3_config['prefix']}/documents/chunked_{document_id}"
            try:
                s3_client.head_object(Bucket=s3_config["bucket"], Key=key)
                return True
            except:
                return False

    except Exception as e:
        logger.error(f"Error checking S3 for {document_id}: {str(e)}")
        return False


def list_s3_documents() -> List[str]:
    """List all documents stored in S3.

    Returns:
        List of document names (without path)
    """
    s3_client = initialize_s3_client()
    if not s3_client:
        return []

    s3_config = get_s3_config()
    if not s3_config:
        return []

    try:
        prefix = f"{s3_config['prefix']}/documents/"
        response = s3_client.list_objects_v2(Bucket=s3_config["bucket"], Prefix=prefix)

        documents = []
        if "Contents" in response:
            for obj in response["Contents"]:
                # Extract just the filename from the full path
                key = obj["Key"]
                filename = key.split("/")[-1]
                documents.append(filename)

        return documents

    except Exception as e:
        logger.error(f"Error listing S3 documents: {str(e)}")
        return []
