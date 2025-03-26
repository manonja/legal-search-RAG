"""Handle document embeddings and vector store operations.

This module provides functionality to generate embeddings using OpenAI's API
and store them in a Chroma vector database for efficient retrieval.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from dotenv import load_dotenv
from tqdm import tqdm
from utils.env import get_chroma_dir, get_chunks_dir

# Load environment variables
load_dotenv()

# Constants
EMBEDDING_MODEL = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-ada-002")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "legal_docs")

# Initialize OpenAI embedding function
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=os.getenv("OPENAI_API_KEY"),
    model_name=EMBEDDING_MODEL,
)


def process_chunks(chunks_dir: Path, chroma_dir: Path) -> None:
    """Process all chunked documents and store their embeddings in Chroma.

    Args:
        chunks_dir: Directory containing chunked text files
        chroma_dir: Directory to store ChromaDB database
    """
    # Initialize Chroma with settings
    chroma_client = chromadb.PersistentClient(
        path=str(chroma_dir),
        settings=Settings(
            anonymized_telemetry=False,
            allow_reset=True,
            is_persistent=True,
        ),
    )

    # Create or get collection with OpenAI embedding function
    collection = chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "Legal document embeddings"},
        embedding_function=openai_ef,
    )

    # Process each chunked file
    chunk_files = list(chunks_dir.glob("chunked_*.txt"))

    if not chunk_files:
        print(f"No chunked files found in {chunks_dir}")
        return

    print(f"Found {len(chunk_files)} chunked files to process")

    for file_path in tqdm(chunk_files, desc="Processing files"):
        doc_id = file_path.stem.replace("chunked_", "")

        with open(file_path, "r", encoding="utf-8") as f:
            text = f.read()
            chunks = text.split("### CHUNK")[1:]  # Split on chunk markers
            chunks = [chunk.strip() for chunk in chunks]

        # Process chunks in batches
        batch_size = 100
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]

            # Generate IDs for batch
            ids = [f"{doc_id}_chunk_{j + i + 1}" for j in range(len(batch))]

            # Add to Chroma (it will handle embeddings through OpenAI)
            try:
                collection.add(
                    ids=ids,
                    documents=batch,
                    metadatas=[{"source": str(file_path)} for _ in batch],
                )
                print(f"Successfully added batch of {len(batch)} chunks")
            except Exception as e:
                print(f"Error processing batch: {e}")
                continue

    print(f"\nProcessing complete! Documents stored in Chroma at {chroma_dir}")


def main() -> None:
    """Process chunks and generate embeddings.

    Reads chunked documents from the specified directory and generates embeddings
    using OpenAI's API, storing them in a Chroma vector database.
    """
    # Get directories from environment utils
    chunks_dir = get_chunks_dir()
    chroma_dir = get_chroma_dir()

    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set")
        return

    print(f"\nProcessing chunks from: {chunks_dir}")
    print(f"Storing embeddings in: {chroma_dir}")
    process_chunks(chunks_dir, chroma_dir)


if __name__ == "__main__":
    main()
