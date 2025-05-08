"""Document processor service.

This package provides modular document processing functionality:
- Loaders: Extract text from different document formats
- Preprocessors: Clean and normalize text
- Chunkers: Split text into semantically coherent sections
"""

from app.services.document_processor.document_processor import DocumentProcessor

__all__ = ["DocumentProcessor"]
