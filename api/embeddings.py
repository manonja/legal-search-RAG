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

# Load environment variables
load_dotenv()

# Constants
EMBEDDING_MODEL = "text-embedding-ada-002"
CACHE_DIR = Path("cache/embeddings")
CHROMA_PERSIST_DIR = Path("cache/chroma")
TENANT_ID = os.getenv("TENANT_ID", "default")
COLLECTION_NAME = f"legal_docs_{TENANT_ID}"

# Initialize OpenAI embedding function
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=os.getenv("OPENAI_API_KEY"),
    model_name=EMBEDDING_MODEL,
)


def get_cached_embedding(text: str, cache_file: Path) -> Optional[List[float]]:
    """Retrieve cached embedding if it exists.

    Args:
        text: The text to get embeddings for
        cache_file: Path to the cache file

    Returns:
        Cached embedding if it exists, None otherwise
    """
    if cache_file.exists():
        with open(cache_file, "r", encoding="utf-8") as f:
            cache: Dict[str, List[float]] = json.load(f)
            return cache.get(text)
    return None


def save_embedding_cache(cache: Dict[str, List[float]], cache_file: Path) -> None:
    """Save embeddings cache to disk.

    Args:
        cache: Dictionary mapping text to embeddings
        cache_file: Path to save cache to
    """
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(cache, f)


def process_chunks(chunks_dir: Path) -> None:
    """Process all chunked documents and store their embeddings in Chroma.

    Args:
        chunks_dir: Directory containing chunked text files
    """
    # Initialize Chroma with settings
    chroma_client = chromadb.PersistentClient(
        path=str(CHROMA_PERSIST_DIR),
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
            ids = [f"{doc_id}_chunk_{j+i+1}" for j in range(len(batch))]

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

    print(f"\nProcessing complete! Documents stored in Chroma at {CHROMA_PERSIST_DIR}")


def main() -> None:
    """Process chunks and generate embeddings.

    Reads chunked documents from the specified directory and generates embeddings
    using OpenAI's API, storing them in a Chroma vector database.
    """
    # Get chunked documents directory from environment with default
    chunks_dir = os.getenv(
        "CHUNKS_DIR", os.path.expanduser("~/Downloads/chunkedLegalDocs")
    )
    chunks_path = Path(chunks_dir)

    if not chunks_path.exists():
        print(f"Error: Chunks directory not found: {chunks_path}")
        return

    if not os.getenv("OPENAI_API_KEY"):
        print("Error: OPENAI_API_KEY environment variable not set")
        return

    print(f"\nProcessing chunks from: {chunks_path}")
    process_chunks(chunks_path)


if __name__ == "__main__":
    main()
