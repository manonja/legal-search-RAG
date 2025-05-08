"""Document loaders.

This module contains loaders for different document formats.
"""

from app.services.document_processor.loaders.pdf_loader import PDFLoader
from app.services.document_processor.loaders.docx_loader import DOCXLoader
from app.services.document_processor.loaders.doc_loader import DOCLoader
from app.services.document_processor.loaders.loader_base import DocumentLoader

__all__ = ["PDFLoader", "DOCXLoader", "DOCLoader", "DocumentLoader"]
