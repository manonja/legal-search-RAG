"""Chunk legal text documents for RAG pipeline.

This script processes text files from an input directory and splits them into smaller,
overlapping chunks suitable for embedding and retrieval.
"""

from pathlib import Path
from typing import List, Optional

from langchain.text_splitter import RecursiveCharacterTextSplitter


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
            out.write(f"### CHUNK {i + 1}\n")
            out.write(chunk)
            out.write("\n\n")

    return len(chunks)
