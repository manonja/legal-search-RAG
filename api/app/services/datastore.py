"""Datastore service for document management.

This module provides an easy API for saving and loading documents:
- Saves original documents with UUID4 names
- Organizes files in a structured directory (settings.DATA_DIR)
- Manages extracted text and metadata
"""

import json
import logging
import os
import shutil
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

from fastapi import UploadFile
from pydantic import BaseModel, Field

from app.core.config import Settings

logger = logging.getLogger(__name__)


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
        logger.info(f"Datastore initialized at {self.data_dir}")

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

        logger.info(f"Document saved: {original_filename} -> {document_id}")
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


def get_datastore_service(settings: Settings) -> DatastoreService:
    """Get a datastore service instance.

    Args:
        settings: Application settings

    Returns:
        DatastoreService instance
    """
    return DatastoreService(settings)
