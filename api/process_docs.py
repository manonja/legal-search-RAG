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

from utils.env import is_gcp_configured
from utils.gcp_storage import download_file, file_exists, list_files, upload_file

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
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable must be set")

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


def get_files_from_gcs(prefix: str = "") -> List[str]:
    """Get list of files from Google Cloud Storage bucket.

    Args:
        prefix: Optional prefix to filter files (e.g., 'input/')

    Returns:
        List of file names in the bucket matching the prefix
    """
    if not is_gcp_configured():
        return []

    # Only return PDF and DOCX files
    files = list_files(prefix)
    return [f for f in files if f.lower().endswith((".pdf", ".docx"))]


def process_gcs_document(gcs_path: str, output_dir: str, model) -> Tuple[bool, str]:
    """Process a single document from Google Cloud Storage.

    Args:
        gcs_path: Path to the document in GCS
        output_dir: Local directory to save the processed output temporarily
        model: Configured Gemini model

    Returns:
        Tuple of (success, message)
    """
    try:
        # Create a temporary directory to download the file
        with tempfile.TemporaryDirectory() as temp_dir:
            # Get just the filename
            filename = os.path.basename(gcs_path)
            temp_file_path = os.path.join(temp_dir, filename)

            # Download the file from GCS
            success, local_path = download_file(gcs_path, temp_file_path)
            if not success:
                return False, f"Failed to download {gcs_path}: {local_path}"

            # Create output filename
            output_filename = f"{os.path.splitext(filename)[0]}.txt"
            temp_output_path = os.path.join(output_dir, output_filename)

            # Check if output already exists in GCS
            output_gcs_path = f"output/{output_filename}"
            if file_exists(output_gcs_path):
                logger.info(
                    f"Output already exists for {filename}, skipping processing"
                )
                return True, f"Skipped {filename} (already processed)"

            # Extract text based on file type
            if filename.lower().endswith(".pdf"):
                file_text = extract_pdf_text(temp_file_path)
            elif filename.lower().endswith(".docx"):
                file_text = extract_docx_text(temp_file_path)
            else:
                return False, f"Unsupported file type: {filename}"

            if not file_text.strip():
                return False, f"No text extracted from {filename}"

            # Build the prompt for the Gemini API
            prompt = (
                "Extract full text from this legal document. "
                "Preserve section numbers, article headers, and numbered paragraphs. "
                "Include any relevant metadata such as parties involved, "
                "jurisdiction, and effective dates.\n\n"
                f"{file_text}"
            )

            # Process with Gemini API
            response = model.generate_content(prompt)

            # Write output to a temporary local file
            os.makedirs(os.path.dirname(temp_output_path), exist_ok=True)
            with open(temp_output_path, "w", encoding="utf-8") as f:
                f.write(response.text)

            # Upload the processed file back to GCS
            success, url = upload_file(temp_output_path, f"output/{output_filename}")
            if not success:
                return False, f"Failed to upload processed file to GCS: {url}"

            return True, f"Successfully processed {filename}"

    except Exception as e:
        return False, f"Error processing {gcs_path}: {str(e)}"


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

    # Check if we should use Google Cloud Storage
    use_gcs = is_gcp_configured()

    if use_gcs:
        logger.info("Using Google Cloud Storage for document processing")
        gcs_files = get_files_from_gcs("input/")

        if not gcs_files:
            logger.warning(
                "No files found in GCS bucket. Make sure you've uploaded files to the 'input/' prefix."
            )

        # Process files from GCS
        for gcs_file in tqdm(gcs_files, desc="Processing GCS documents"):
            gcs_path = f"input/{gcs_file}"
            success, msg = process_gcs_document(gcs_path, output_dir, model)
            if success:
                logger.info(msg)
            else:
                logger.error(msg)

    # Process local files regardless of GCS configuration
    # This allows for hybrid operation
    files = [f for f in os.listdir(input_dir) if f.lower().endswith((".pdf", ".docx"))]

    for filename in tqdm(files, desc="Processing local documents"):
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

            # If GCS is configured, also upload the processed file to GCS
            if use_gcs:
                gcs_output_path = f"output/{os.path.basename(output_file)}"
                success, url = upload_file(output_file, gcs_output_path)
                if success:
                    logger.info(f"Uploaded processed file to GCS: {url}")
                else:
                    logger.error(f"Failed to upload to GCS: {url}")

        except Exception as e:
            logger.error(f"Failed to process {filename}: {e}")


def main():
    """Execute the main document processing workflow.

    This function orchestrates the document processing workflow:
    1. Gets input/output directories from environment variables
    2. Processes documents using the Gemini API

    Raises:
        ValueError: If required environment variables are not set
        Exception: For any other unexpected errors during processing
    """
    try:
        # Get input and output directories from environment variables
        input_directory = os.getenv("INPUT_DIR")
        output_directory = os.getenv("OUTPUT_DIR")

        if not input_directory or not output_directory:
            raise ValueError(
                "INPUT_DIR and OUTPUT_DIR environment variables must be set"
            )

        # Process the documents
        process_documents(input_directory, output_directory)

    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        exit(1)
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        exit(1)


if __name__ == "__main__":
    main()
