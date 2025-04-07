"""Datastore service for document management.

This module provides an easy API for saving and loading documents:
- Saves original documents with UUID4 names
- Organizes files in a structured directory (settings.DATA_DIR)
- Manages extracted text and metadata
"""

import json
import os
import shutil
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from fastapi import UploadFile
from pydantic import BaseModel, Field

from app.core.config import Settings
from app.core.struct_logger import log


class DocumentMetadata(BaseModel):
    """Metadata for a stored document."""

    document_id: str = Field(..., description="Unique document identifier (UUID4)")
    original_filename: str = Field(..., description="Original uploaded filename")
    original_file_path: str = Field(..., description="Path to the stored original file")
    text_file_path: Optional[str] = Field(
        None, description="Path to the extracted text file"
    )
    document_dir: str = Field(
        ..., description="Directory containing the document files"
    )

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "document_id": "123e4567-e89b-12d3-a456-426614174000",
                "original_filename": "contract.pdf",
                "original_file_path": "/data/123e4567-e89b-12d3-a456-426614174000/original.pdf",
                "text_file_path": "/data/123e4567-e89b-12d3-a456-426614174000/extracted_text.txt",
                "document_dir": "/data/123e4567-e89b-12d3-a456-426614174000",
            }
        }

    def __getitem__(self, key: str) -> Any:
        """Support dictionary-like access for backward compatibility.

        Args:
            key: The attribute name to access

        Returns:
            The attribute value

        Raises:
            KeyError: If the attribute doesn't exist
        """
        try:
            return getattr(self, key)
        except AttributeError as err:
            raise KeyError(key) from err

    def get(self, key: str, default: Any = None) -> Any:
        """Dictionary-like get method with default value.

        Args:
            key: The attribute name to access
            default: Default value if attribute doesn't exist

        Returns:
            The attribute value or default
        """
        try:
            return getattr(self, key)
        except AttributeError:
            return default


class DatastoreService:
    """Service for managing document storage and retrieval."""

    def __init__(self, settings: Settings):
        """Initialize the datastore service.

        Args:
            settings: Application settings
        """
        self.settings = settings
        self.data_dir = settings.DATA_DIR
        self._ensure_data_directory_exists()

    def _ensure_data_directory_exists(self) -> None:
        """Ensure the data directory structure exists."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        log.info("Datastore initialized", data_dir=str(self.data_dir))

    def _create_document_directory(self, document_id: str) -> Path:
        """Create a directory for the document.

        Args:
            document_id: Unique document identifier (UUID4)

        Returns:
            Path to the created directory
        """
        doc_dir = self.data_dir / document_id
        doc_dir.mkdir(parents=True, exist_ok=True)
        return doc_dir

    async def save_document(
        self, file: UploadFile, text_content: str = ""
    ) -> DocumentMetadata:
        """Save a document to the datastore.

        Args:
            file: The uploaded file to save
            text_content: Extracted text content from the document

        Returns:
            DocumentMetadata with information about the saved document
        """
        # Generate a UUID for the document
        document_id = str(uuid.uuid4())

        # Create document directory
        doc_dir = self._create_document_directory(document_id)

        # Save original file with its original name
        original_filename = file.filename

        if original_filename is None:
            raise ValueError("Original filename is required")

        original_file_path = doc_dir / original_filename

        # Reset file position if needed
        await file.seek(0)
        content = await file.read()

        with open(original_file_path, "wb") as f:
            f.write(content)

        # Save extracted text if provided
        text_file_path = None
        if text_content:
            text_file_path = doc_dir / "extracted_text.txt"
            with open(text_file_path, "w", encoding="utf-8") as f:
                f.write(text_content)

        # Create metadata
        metadata = DocumentMetadata(
            document_id=document_id,
            original_filename=original_filename,
            original_file_path=str(original_file_path),
            text_file_path=str(text_file_path) if text_file_path else None,
            document_dir=str(doc_dir),
        )

        # Save metadata to file
        with open(doc_dir / "metadata.json", "w", encoding="utf-8") as f:
            f.write(metadata.model_dump_json(indent=2))

        log.info("Document saved", filename=original_filename, document_id=document_id)
        return metadata

    def get_document(self, document_id: str) -> Optional[DocumentMetadata]:
        """Retrieve document metadata by document_id.

        Args:
            document_id: Unique document identifier (UUID4)

        Returns:
            DocumentMetadata if found, None otherwise
        """
        doc_dir = self.data_dir / document_id

        if not doc_dir.exists():
            return None

        metadata_file = doc_dir / "metadata.json"
        if not metadata_file.exists():
            return None

        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata_dict = json.load(f)
            return DocumentMetadata.model_validate(metadata_dict)

    def get_original_file_path(self, document_id: str) -> Optional[Path]:
        """Get the path to the original document.

        Args:
            document_id: Unique document identifier (UUID4)

        Returns:
            Path to the original file if found, None otherwise
        """
        metadata = self.get_document(document_id)
        if not metadata or not metadata.original_file_path:
            return None

        path = Path(metadata.original_file_path)
        return path if path.exists() else None

    def get_text_content(self, document_id: str) -> Optional[str]:
        """Get the extracted text content for a document.

        Args:
            document_id: Unique document identifier (UUID4)

        Returns:
            Extracted text content if available, None otherwise
        """
        metadata = self.get_document(document_id)
        if not metadata or not metadata.text_file_path:
            return None

        text_path = Path(metadata.text_file_path)
        if not text_path.exists():
            return None

        with open(text_path, "r", encoding="utf-8") as f:
            return f.read()

    def list_document_ids(self) -> List[str]:
        """List all document IDs available in the datastore."""
        document_ids = []
        for entry in self.data_dir.iterdir():
            if entry.is_dir():
                # Check if it looks like a UUID directory and has metadata
                try:
                    uuid.UUID(entry.name)  # Check if the name is a valid UUID
                    metadata_file = entry / "metadata.json"
                    if metadata_file.exists():
                        document_ids.append(entry.name)
                except ValueError:
                    # Not a UUID-named directory, skip
                    continue
        log.info("Listed document IDs", count=len(document_ids))
        return document_ids

    def delete_document(self, document_id: str) -> bool:
        """Delete a document and its associated files.

        Args:
            document_id: The ID of the document to delete.

        Returns:
            True if the document was deleted, False otherwise.
        """
        doc_dir = self.data_dir / document_id
        if not doc_dir.exists() or not doc_dir.is_dir():
            log.warning(
                "Attempted to delete non-existent document", document_id=document_id
            )
            return False

        try:
            # First, delete document chunks from ChromaDB
            try:
                from app.core.config import get_settings
                from app.services.database.chroma import get_chroma_client

                settings = get_settings()
                # Get ChromaDB client
                chroma_client = get_chroma_client()

                # Get the collection
                collection = chroma_client.get_collection(name=settings.COLLECTION_NAME)

                # Use the where filter to find and delete all chunks with this document_id
                collection.delete(where={"document_id": document_id})

                log.info(
                    "Deleted document chunks from ChromaDB", document_id=document_id
                )
            except Exception as e:
                log.warning(
                    "Error deleting document chunks from ChromaDB",
                    document_id=document_id,
                    error=str(e),
                    exc_info=True,
                )
                # Continue with file deletion even if ChromaDB deletion fails

            # Then delete files from filesystem
            shutil.rmtree(doc_dir)
            log.info("Document deleted successfully", document_id=document_id)
            return True
        except OSError as e:
            log.error(
                "Error deleting document directory",
                document_id=document_id,
                error=str(e),
                exc_info=True,
            )
            return False


def get_datastore_service(settings: Settings) -> DatastoreService:
    """Get a datastore service instance.

    Args:
        settings: Application settings

    Returns:
        DatastoreService instance
    """
    return DatastoreService(settings)
