"""Base document loader.

This module defines the base class for document loaders.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional


class DocumentLoader(ABC):
    """Base class for document loaders."""

    @abstractmethod
    def load(self, file_path: Path) -> tuple[str, Dict[str, Any]]:
        """Load document and extract text.

        Args:
            file_path: Path to the document file

        Returns:
            Tuple containing extracted text and document metadata
        """
        pass

    @classmethod
    def get_loader_for_file(cls, file_path: Path, content_type: Optional[str] = None):
        """Factory method to get appropriate loader for a file.

        Args:
            file_path: Path to the document file
            content_type: Optional MIME content type

        Returns:
            Appropriate document loader instance
        """
        from app.services.document_processor.loaders import (
            PDFLoader,
            DOCXLoader,
            DOCLoader,
        )

        # First try using content_type
        if content_type:
            if content_type == "application/pdf":
                return PDFLoader()
            elif (
                content_type
                == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ):
                return DOCXLoader()
            elif content_type == "application/msword":
                return DOCLoader()

        # Fallback to file extension
        file_extension = file_path.suffix.lower()
        if file_extension == ".pdf":
            return PDFLoader()
        elif file_extension == ".docx":
            return DOCXLoader()
        elif file_extension == ".doc":
            return DOCLoader()

        raise ValueError(
            f"Unsupported file type: {file_path} with content type {content_type}"
        )
