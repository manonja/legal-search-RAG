import json
import logging
import os
import tempfile
from typing import Any, Dict, List

import docx
import fitz  # PyMuPDF
from tqdm import tqdm

from .storage import GCPStorage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Process documents and store their content for embedding and search"""

    def __init__(self, tenant_id: str):
        """Initialize with tenant isolation"""
        self.tenant_id = tenant_id
        self.storage = GCPStorage(tenant_id)
        self.local_docs_path = f"cache/documents/{tenant_id}"

        # Ensure local directory exists
        os.makedirs(self.local_docs_path, exist_ok=True)

    def process_document(self, file_path: str, document_id: str = None) -> Dict[str, Any]:
        """Process a document and return its metadata"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {file_path} not found")

        file_name = os.path.basename(file_path)
        file_ext = os.path.splitext(file_name)[1].lower()

        # Generate document ID if not provided
        if not document_id:
            document_id = os.path.splitext(file_name)[0]

        # Extract text based on file type
        if file_ext == '.pdf':
            text, metadata = self._process_pdf(file_path)
        elif file_ext in ['.docx', '.doc']:
            text, metadata = self._process_docx(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_ext}")

        # Create document metadata
        doc_metadata = {
            "id": document_id,
            "filename": file_name,
            "extension": file_ext,
            "size_bytes": os.path.getsize(file_path),
            "text_length": len(text),
            **metadata
        }

        # Store document text
        text_path = os.path.join(self.local_docs_path, f"{document_id}.txt")
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(text)

        # Store document metadata
        metadata_path = os.path.join(self.local_docs_path, f"{document_id}.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(doc_metadata, f, indent=2)

        # Upload to GCP Storage
        self.storage.upload_document(file_path, f"{document_id}{file_ext}")
        self.storage.upload_document(text_path, f"{document_id}.txt")
        self.storage.upload_document(metadata_path, f"{document_id}.json")

        logger.info(f"Processed document {file_name} with ID {document_id}")

        return doc_metadata

    def download_and_process_document(self, gcs_blob_name: str) -> Dict[str, Any]:
        """Download a document from GCP and process it"""
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            # Download document from GCP
            self.storage.download_document(gcs_blob_name, temp_path)

            # Process the document
            document_id = os.path.splitext(gcs_blob_name)[0]
            return self.process_document(temp_path, document_id)

        finally:
            # Clean up the temporary file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def list_processed_documents(self) -> List[Dict[str, Any]]:
        """List all processed documents for this tenant"""
        documents = []

        # Get all JSON metadata files from the local cache
        for filename in os.listdir(self.local_docs_path):
            if filename.endswith('.json'):
                with open(os.path.join(self.local_docs_path, filename), 'r') as f:
                    doc_metadata = json.load(f)
                    documents.append(doc_metadata)

        return documents

    def _process_pdf(self, file_path: str) -> tuple:
        """Extract text and metadata from a PDF file"""
        text = ""
        metadata = {}

        try:
            with fitz.open(file_path) as doc:
                # Extract metadata
                metadata = {
                    "title": doc.metadata.get("title", ""),
                    "author": doc.metadata.get("author", ""),
                    "page_count": len(doc),
                    "creation_date": doc.metadata.get("creationDate", "")
                }

                # Extract text from each page
                for page in tqdm(doc, desc="Processing PDF pages"):
                    text += page.get_text()

        except Exception as e:
            logger.error(f"Error processing PDF {file_path}: {e}")
            raise

        return text, metadata

    def _process_docx(self, file_path: str) -> tuple:
        """Extract text and metadata from a DOCX file"""
        text = ""
        metadata = {}

        try:
            doc = docx.Document(file_path)

            # Extract metadata from core properties
            try:
                core_props = doc.core_properties
                metadata = {
                    "title": core_props.title or "",
                    "author": core_props.author or "",
                    "page_count": len(doc.sections),
                    "creation_date": str(core_props.created) if core_props.created else ""
                }
            except:
                metadata = {
                    "title": "",
                    "author": "",
                    "page_count": len(doc.sections)
                }

            # Extract text from paragraphs
            for para in tqdm(doc.paragraphs, desc="Processing DOCX paragraphs"):
                text += para.text + "\n"

        except Exception as e:
            logger.error(f"Error processing DOCX {file_path}: {e}")
            raise

        return text, metadata
