"""Module for converting and processing legal documents for the RAG system.

This module provides functionality to convert various document formats.
into a format suitable for processing in the legal document search RAG system.
It handles document parsing, text extraction, and prepare vector storage.
"""

import logging
import os
import tempfile
from typing import List, Tuple

import docx  # python-docx package
import fitz  # PyMuPDF
import google.generativeai as genai  # type: ignore
from tqdm import tqdm  # type: ignore
from utils.env import get_google_api_key, get_input_dir, get_output_dir

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def configure_gemini():
    """Configure and initialize the Gemini model.

    Returns:
        GenerativeModel: Configured Gemini model instance ready for text
        generation.
    """
    api_key = get_google_api_key()
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-1.5-flash")


def extract_pdf_text(file_path):
    """Extract text from a PDF file using PyMuPDF (fitz)."""
    text = ""
    try:
        doc = fitz.open(file_path)
        for page in doc:
            text += page.get_text("text")  # Extract text from each page
    except Exception as e:
        logger.error(f"Error extracting PDF {file_path}: {e}")
    return text


def extract_docx_text(file_path):
    """Extract text from a DOCX file using python-docx."""
    text = ""
    try:
        doc = docx.Document(file_path)
        text = "\n".join(para.text for para in doc.paragraphs)
    except Exception as e:
        logger.error(f"Error extracting DOCX {file_path}: {e}")
    return text


def process_documents(input_dir: str, output_dir: str) -> None:
    """Process legal documents and extract their content using Gemini.

    Args:
        input_dir: Directory containing the input PDF and DOCX files.
        output_dir: Directory where the processed text files will be saved.
    """
    model = configure_gemini()

    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Process local files
    files = [f for f in os.listdir(input_dir) if f.lower().endswith((".pdf", ".docx"))]

    if not files:
        logger.warning(f"No PDF or DOCX files found in {input_dir}")
        return

    logger.info(f"Found {len(files)} documents to process")

    for filename in tqdm(files, desc="Processing documents"):
        file_path = os.path.join(input_dir, filename)
        output_file = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}.txt")

        # Skip files that have already been processed
        if os.path.exists(output_file):
            logger.info(f"Skipping already processed file: {filename}")
            continue

        # Extract text based on file type
        if filename.lower().endswith(".pdf"):
            file_text = extract_pdf_text(file_path)
        elif filename.lower().endswith(".docx"):
            file_text = extract_docx_text(file_path)
        else:
            continue  # Skip unsupported file types

        if not file_text.strip():
            logger.warning(f"No text extracted from {filename}. Skipping...")
            continue

        # Build the prompt for the Gemini API
        prompt = (
            "Extract full text from this legal document. "
            "Preserve section numbers, article headers, and numbered paragraphs. "
            "Include any relevant metadata such as parties involved, "
            "jurisdiction, and effective dates.\n\n"
            f"{file_text}"
        )

        try:
            # Send the prompt to the Gemini API for further processing
            response = model.generate_content(prompt)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(response.text)
            logger.info(f"Processed: {filename}")

        except Exception as e:
            logger.error(f"Failed to process {filename}: {e}")


def main():
    """Execute the main document processing workflow.

    This function orchestrates the document processing workflow:
    1. Gets input/output directories from environment variables
    2. Processes documents using Gemini API
    """
    # Get input/output directories from environment variables
    input_dir = get_input_dir()
    output_dir = get_output_dir()

    logger.info(f"Input directory: {input_dir}")
    logger.info(f"Output directory: {output_dir}")

    process_documents(str(input_dir), str(output_dir))
    logger.info("Document processing complete!")


if __name__ == "__main__":
    main()
