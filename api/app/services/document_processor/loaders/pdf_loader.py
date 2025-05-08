"""PDF document loader.

This module provides functionality to extract text from PDF documents.
"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import Dict, Any

from app.core.struct_logger import log
from app.services.document_processor.loaders.loader_base import DocumentLoader


class PDFLoader(DocumentLoader):
    """Loader for PDF documents using PyMuPDF (fitz)."""

    def load(self, file_path: Path) -> tuple[str, Dict[str, Any]]:
        """Extract text from a PDF file.

        Args:
            file_path: Path to the PDF file

        Returns:
            Tuple containing extracted text and document metadata
        """
        text = ""
        metadata = {"original_file_type": "pdf"}

        try:
            doc = fitz.open(file_path)

            # Extract document metadata
            pdf_metadata = doc.metadata
            if pdf_metadata:
                for key, value in pdf_metadata.items():
                    if value:
                        metadata[f"pdf_{key.lower()}"] = value

            # Extract text from each page
            for page in doc:
                text += page.get_text("text")  # type: ignore

            # Add page count to metadata
            metadata["page_count"] = len(doc)

        except Exception as e:
            log.error("Error extracting PDF", file_path=str(file_path), error=str(e))
            raise ValueError(f"Failed to extract text from PDF: {str(e)}") from e

        return text, metadata
