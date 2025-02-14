"""Chunk legal text documents for RAG pipeline.

This script processes text files from an input directory and splits them into smaller,
overlapping chunks suitable for embedding and retrieval.
"""

import os
from pathlib import Path
from typing import List, Optional

from langchain.text_splitter import RecursiveCharacterTextSplitter
from tqdm import tqdm


def create_text_splitter(
    chunk_size: int = 512,
    chunk_overlap: int = 50,
    separators: Optional[List[str]] = None,
) -> RecursiveCharacterTextSplitter:
    """Create a RecursiveCharacterTextSplitter with specified parameters.

    Args:
        chunk_size: Maximum number of characters per chunk
        chunk_overlap: Number of characters to overlap between chunks
        separators: List of separators to use for splitting, in order of preference

    Returns:
        Configured RecursiveCharacterTextSplitter instance
    """
    if separators is None:
        separators = ["\n\n", "\n", " ", ""]

    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=separators,
    )


def process_file(
    input_path: Path,
    output_path: Path,
    text_splitter: RecursiveCharacterTextSplitter,
) -> int:
    """Process a single text file and split it into chunks.

    Args:
        input_path: Path to input text file
        output_path: Path to output chunked file
        text_splitter: Configured text splitter instance

    Returns:
        Number of chunks created
    """
    with open(input_path, "r", encoding="utf-8") as file:
        text = file.read()

    chunks = text_splitter.split_text(text)

    with open(output_path, "w", encoding="utf-8") as out:
        for i, chunk in enumerate(chunks):
            out.write(f"### CHUNK {i+1}\n")
            out.write(chunk)
            out.write("\n\n")

    return len(chunks)


def main():
    """Process all text files in the input directory.

    Uses environment variables:
        - INPUT_DIR: Directory containing processed legal text files
        - OUTPUT_DIR: Directory to save chunked output files
    """
    # Get input/output directories from environment variables with defaults
    input_dir = os.getenv(
        "INPUT_DIR", os.path.expanduser("~/Downloads/processedLegalDocs")
    )
    output_dir = os.getenv(
        "OUTPUT_DIR", os.path.expanduser("~/Downloads/chunkedLegalDocs")
    )

    input_path = Path(input_dir)
    output_path = Path(output_dir)

    if not input_path.exists():
        print(f"Error: Input directory not found: {input_path}")
        return

    output_path.mkdir(exist_ok=True, parents=True)
    print(f"\nInput directory: {input_path}")
    print(f"Output directory: {output_path}\n")

    text_splitter = create_text_splitter()

    # Get list of all .txt files
    txt_files = list(input_path.glob("*.txt"))

    if not txt_files:
        print(f"No .txt files found in {input_dir}")
        return

    print(f"Found {len(txt_files)} text files to process")

    total_chunks = 0
    for file_path in tqdm(txt_files, desc="Processing files"):
        output_file = output_path / f"chunked_{file_path.name}"
        num_chunks = process_file(file_path, output_file, text_splitter)
        total_chunks += num_chunks

    print("\nProcessing complete!")
    print(f"Total files processed: {len(txt_files)}")
    print(f"Total chunks created: {total_chunks}")
    print(f"Chunked files saved in: {output_path.absolute()}")


if __name__ == "__main__":
    main()
