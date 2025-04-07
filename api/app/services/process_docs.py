"""Module for converting and processing legal documents for the RAG system.

This module provides functionality to extract text from various document formats
for processing in the legal document search RAG system.
It handles document parsing and text extraction.
"""

import os
import shlex
import subprocess
from pathlib import Path

import docx  # python-docx package
import fitz  # PyMuPDF

from app.core.struct_logger import log


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


def extract_doc_text(file_path):
    """Extract text from a DOC file using antiword.

    Note: This requires the antiword utility to be installed on the system.
    """
    text = ""
    try:
        # Validate the file path to ensure it exists and is a file
        file_path_obj = Path(file_path)
        if not file_path_obj.is_file():
            raise ValueError(f"File not found: {file_path}")

        # Verify file extension is .doc
        if not str(file_path_obj).lower().endswith(".doc"):
            raise ValueError(f"File does not have .doc extension: {file_path}")

        # Additional validation - check file size is reasonable (prevent huge files)
        file_size = file_path_obj.stat().st_size
        if file_size > 50 * 1024 * 1024:  # 50 MB limit
            raise ValueError(f"File too large to process: {file_size} bytes")

        # Get the full path to antiword executable
        antiword_path = "/usr/bin/antiword"  # Default path on Linux/Docker
        if not os.path.exists(antiword_path):
            # Try macOS Homebrew location
            antiword_path = "/usr/local/bin/antiword"
            if not os.path.exists(antiword_path):
                # Last resort, use PATH resolution (less secure but may be necessary)
                antiword_path = "antiword"

        # Call antiword as a subprocess with validated inputs
        # We have fully validated the inputs above, so this is safe
        result = subprocess.run(  # noqa: S603
            [antiword_path, str(file_path_obj)],
            capture_output=True,
            text=True,
            check=True,
        )
        text = result.stdout
    except subprocess.CalledProcessError as e:
        log.error("Error running antiword", file_path=file_path, error=str(e))
    except Exception as e:
        log.error("Error extracting DOC", file_path=file_path, error=str(e))
    return text
