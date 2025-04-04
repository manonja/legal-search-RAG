"""Module for converting and processing legal documents for the RAG system.

This module provides functionality to extract text from various document formats
for processing in the legal document search RAG system.
It handles document parsing and text extraction.
"""

import docx  # python-docx package
import fitz  # PyMuPDF
from struct_logger import log


def extract_pdf_text(file_path):
    """Extract text from a PDF file using PyMuPDF (fitz)."""
    text = ""
    try:
        doc = fitz.open(file_path)
        for page in doc:
            text += page.get_text("text")  # type: ignore # Extract text from each page
    except Exception as e:
        log.error("Error extracting PDF", file_path=file_path, error=str(e))
    return text


def extract_docx_text(file_path):
    """Extract text from a DOCX file using python-docx."""
    text = ""
    try:
        doc = docx.Document(file_path)
        text = "\n".join(para.text for para in doc.paragraphs)
    except Exception as e:
        log.error("Error extracting DOCX", file_path=file_path, error=str(e))
    return text
