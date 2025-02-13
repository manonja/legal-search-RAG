"""Module for converting and processing legal documents for the RAG system.

This module provides functionality to convert various document formats.
into a format suitable for processing in the legal document search RAG system.
It handles document parsing, text extraction, and prepare vector storage.
"""

import os

import google.generativeai as genai  # type: ignore
from tqdm import tqdm  # type: ignore


def configure_gemini():
    """Configure and initialize the Gemini model.

    Returns:
        GenerativeModel: Configured Gemini model instance ready for text
        generation.
    """
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    return genai.GenerativeModel("gemini-1.5-flash")


def process_documents(input_dir, output_dir):
    """Process legal documents and extract their content using Gemini.

    Args:
        input_dir: Directory containing the input PDF and DOCX files.
        output_dir: Directory where the processed text files will be saved.
    """
    model = configure_gemini()

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for filename in tqdm(os.listdir(input_dir), desc="Processing documents"):
        if filename.endswith((".pdf", ".docx")):
            file_path = os.path.join(input_dir, filename)
            try:
                prompt = (
                    f"Extract full text from this legal document '{filename}'. "
                    "Preserve section numbers, article headers, and numbered "
                    "paragraphs. Include any relevant metadata such as parties "
                    "involved, jurisdiction, and effective dates."
                )
                response = model.generate_content([prompt, file_path])

                output_file = os.path.join(
                    output_dir, f"{os.path.splitext(filename)[0]}.txt"
                )
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(response.text)
                print(f"Processed: {filename}")
            except Exception as e:
                print(f"Failed to process {filename}: {e}")


if __name__ == "__main__":
    input_directory = "/Users/manonjacquin/Downloads/legaldocs"
    output_directory = "/Users/manonjacquin/Downloads/processedLegalDocs"
    process_documents(input_directory, output_directory)
