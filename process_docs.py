"""Module for converting and processing legal documents for the RAG system.

This module provides functionality to convert various document formats.
into a format suitable for processing in the legal document search RAG system.
It handles document parsing, text extraction, and prepare vector storage.
"""

import os

import docx  # python-docx package
import fitz  # PyMuPDF
import google.generativeai as genai  # type: ignore
from tqdm import tqdm  # type: ignore

from utils.env import get_google_api_key, get_input_dir, get_output_dir, load_env


def configure_gemini():
    """Configure and initialize the Gemini model.

    Returns:
        GenerativeModel: Configured Gemini model instance ready for text
        generation.
    """
    genai.configure(api_key=get_google_api_key())
    return genai.GenerativeModel("gemini-1.5-flash")


def extract_pdf_text(file_path):
    """Extract text from a PDF file using PyMuPDF (fitz)."""
    text = ""
    try:
        doc = fitz.open(file_path)
        for page in doc:
            text += page.get_text("text")  # Extract text from each page
    except Exception as e:
        print(f"Error extracting PDF {file_path}: {e}")
    return text


def extract_docx_text(file_path):
    """Extract text from a DOCX file using python-docx."""
    text = ""
    try:
        doc = docx.Document(file_path)
        text = "\n".join(para.text for para in doc.paragraphs)
    except Exception as e:
        print(f"Error extracting DOCX {file_path}: {e}")
    return text


def process_documents(input_dir: str, output_dir: str) -> None:
    """Process legal documents and extract their content using Gemini.

    Args:
        input_dir: Directory containing the input PDF and DOCX files.
        output_dir: Directory where the processed text files will be saved.
    """
    model = configure_gemini()

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Filter files
    files = [f for f in os.listdir(input_dir) if f.lower().endswith((".pdf", ".docx"))]

    for filename in tqdm(files, desc="Processing documents"):
        file_path = os.path.join(input_dir, filename)
        output_file = os.path.join(output_dir, f"{os.path.splitext(filename)[0]}.txt")

        # Skip files that have already been processed
        if os.path.exists(output_file):
            print(f"Skipping already processed file: {filename}")
            continue

        # Extract text based on file type
        if filename.lower().endswith(".pdf"):
            file_text = extract_pdf_text(file_path)
        elif filename.lower().endswith(".docx"):
            file_text = extract_docx_text(file_path)
        else:
            continue  # Skip unsupported file types

        if not file_text.strip():
            print(f"No text extracted from {filename}. Skipping...")
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
            print(f"Processed: {filename}")

            # Optional: introduce a small delay to avoid rapid API calls
            # time.sleep(1)

        except Exception as e:
            print(f"Failed to process {filename}: {e}")


def main():
    """Execute the main document processing workflow.

    This function orchestrates the document processing workflow:
    1. Loads and validates environment variables
    2. Sets up input/output directories
    3. Processes documents using the Gemini API

    Raises:
        FileNotFoundError: If the .env file is missing
        ValueError: If required environment variables are not set
        Exception: For any other unexpected errors during processing
    """
    try:
        # Load and validate environment variables
        load_env(validate=True)

        # Get input and output directories
        input_directory = get_input_dir()
        output_directory = get_output_dir()

        # Process the documents
        process_documents(input_directory, output_directory)

    except (FileNotFoundError, ValueError) as e:
        print(f"Configuration error: {e}")
        exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        exit(1)


if __name__ == "__main__":
    main()
