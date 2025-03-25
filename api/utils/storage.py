import json
import logging
import os
import shutil
import tempfile

from dotenv import load_dotenv
from google.cloud import storage

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GCPStorage:
    def __init__(self, tenant_id):
        """Initialize GCP storage client with tenant isolation."""
        self.tenant_id = tenant_id
        self.is_mock = False
        self.local_storage_path = os.path.join("cache", "gcp_mock_storage", tenant_id)

        try:
            # Check for valid credentials
            credentials_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")

            if not credentials_path or not os.path.exists(credentials_path):
                self._fallback_to_mock_storage()
                return

            # Check if credentials file is a placeholder
            with open(credentials_path, 'r') as f:
                content = f.read().strip()
                if content == "{}" or not content:
                    self._fallback_to_mock_storage()
                    return

            # Initialize GCP client
            self.client = storage.Client()
            self.bucket_name = os.getenv("GCS_BUCKET_NAME", f"legal-search-{tenant_id}")

            # Ensure the bucket exists
            try:
                self.bucket = self.client.get_bucket(self.bucket_name)
                logger.info(f"Connected to GCP bucket: {self.bucket_name}")
            except Exception as e:
                logger.error(f"Error accessing GCS bucket: {e}")
                self._fallback_to_mock_storage()

        except Exception as e:
            logger.error(f"Error initializing GCP storage: {e}")
            self._fallback_to_mock_storage()

    def _fallback_to_mock_storage(self):
        """Fall back to local file system if GCP storage is not available"""
        self.is_mock = True
        logger.warning("GCP credentials not available. Falling back to local storage.")

        # Create local storage directory
        os.makedirs(self.local_storage_path, exist_ok=True)
        logger.info(f"Using mock storage at: {self.local_storage_path}")

    def upload_document(self, file_path, destination_blob_name=None):
        """Upload a document to GCP storage with tenant prefix."""
        if not destination_blob_name:
            destination_blob_name = os.path.basename(file_path)

        # Create tenant-specific path
        tenant_blob_path = f"{self.tenant_id}/documents/{destination_blob_name}"

        if self.is_mock:
            # Copy file to local storage
            dest_path = os.path.join(self.local_storage_path, "documents", destination_blob_name)
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            shutil.copy2(file_path, dest_path)
            logger.info(f"[MOCK] File {file_path} copied to {dest_path}")
            return tenant_blob_path

        # Use actual GCP storage
        blob = self.bucket.blob(tenant_blob_path)
        blob.upload_from_filename(file_path)

        logger.info(f"File {file_path} uploaded to {tenant_blob_path}")
        return tenant_blob_path

    def download_document(self, blob_name, destination_file_path):
        """Download a document from GCP storage."""
        # Get the full tenant path
        tenant_blob_path = f"{self.tenant_id}/documents/{blob_name}"

        if self.is_mock:
            # Copy file from local storage
            source_path = os.path.join(self.local_storage_path, "documents", blob_name)
            if not os.path.exists(source_path):
                raise FileNotFoundError(f"[MOCK] File not found: {source_path}")

            os.makedirs(os.path.dirname(destination_file_path), exist_ok=True)
            shutil.copy2(source_path, destination_file_path)
            logger.info(f"[MOCK] Downloaded {source_path} to {destination_file_path}")
            return destination_file_path

        # Use actual GCP storage
        blob = self.bucket.blob(tenant_blob_path)
        blob.download_to_filename(destination_file_path)

        logger.info(f"Downloaded {tenant_blob_path} to {destination_file_path}")
        return destination_file_path

    def list_documents(self):
        """List all documents for a specific tenant."""
        if self.is_mock:
            # List files from local storage
            docs_dir = os.path.join(self.local_storage_path, "documents")
            if not os.path.exists(docs_dir):
                return []

            return [f for f in os.listdir(docs_dir) if os.path.isfile(os.path.join(docs_dir, f))]

        # Use actual GCP storage
        prefix = f"{self.tenant_id}/documents/"
        blobs = self.client.list_blobs(self.bucket_name, prefix=prefix)

        return [blob.name.replace(prefix, '') for blob in blobs]

    def delete_document(self, blob_name):
        """Delete a document from GCP storage."""
        tenant_blob_path = f"{self.tenant_id}/documents/{blob_name}"

        if self.is_mock:
            # Delete file from local storage
            source_path = os.path.join(self.local_storage_path, "documents", blob_name)
            if not os.path.exists(source_path):
                logger.warning(f"[MOCK] File not found for deletion: {source_path}")
                return False

            os.remove(source_path)
            logger.info(f"[MOCK] Deleted {source_path}")
            return True

        # Use actual GCP storage
        blob = self.bucket.blob(tenant_blob_path)
        blob.delete()

        logger.info(f"Deleted {tenant_blob_path}")
        return True
