"""Query interface for the legal document RAG system.

This module provides functionality to query the Chroma vector database
and retrieve relevant legal document chunks based on semantic similarity.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Constants
EMBEDDING_MODEL = "text-embedding-ada-002"
CHROMA_PERSIST_DIR = Path("cache/chroma")
DEFAULT_NUM_RESULTS = 5  # Number of chunks to retrieve per query

# Initialize OpenAI embedding function
openai_ef = OpenAIEmbeddingFunction(
    api_key=os.getenv("OPENAI_API_KEY"),
    model_name=EMBEDDING_MODEL,
)


def get_chroma_client() -> chromadb.PersistentClient:
    """Initialize and return a persistent Chroma client.

    Returns:
        chromadb.PersistentClient: Initialized Chroma client
    """
    return chromadb.PersistentClient(
        path=str(CHROMA_PERSIST_DIR),
        settings=Settings(
            anonymized_telemetry=False,
            allow_reset=True,
            is_persistent=True,
        ),
    )


def get_collection(client: chromadb.PersistentClient) -> chromadb.Collection:
    """Get the legal documents collection.

    Args:
        client: Initialized Chroma client

    Returns:
        Collection: Chroma collection for legal documents
    """
    return client.get_collection(
        name="legal_docs",
        embedding_function=openai_ef,
    )


def query_documents(
    query_text: str,
    n_results: int = DEFAULT_NUM_RESULTS,
    metadata_filter: Optional[Dict[str, Any]] = None,
    min_similarity: float = 0.0,
) -> List[Dict[str, Any]]:
    """Query the document collection and return relevant chunks.

    Args:
        query_text: The text to search for
        n_results: Number of results to return
        metadata_filter: Optional filter for document metadata
        min_similarity: Minimum similarity threshold (0 to 1)

    Returns:
        List of dictionaries containing matched chunks and their metadata
    """
    client = get_chroma_client()
    collection = get_collection(client)

    # Perform the query
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results,
        where=metadata_filter,  # Apply metadata filter if provided
        include=["documents", "metadatas", "distances"],
    )

    # Process and format results
    formatted_results = []
    for idx, (doc, metadata, distance) in enumerate(
        zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )
    ):
        # Convert distance to similarity score (0 to 1)
        similarity = 1 - (distance / 2)  # Normalize distance to similarity

        # Skip results below similarity threshold
        if similarity < min_similarity:
            continue

        formatted_results.append(
            {
                "chunk": doc,
                "metadata": metadata,
                "similarity": similarity,
                "rank": idx + 1,
            }
        )

    return formatted_results


def main() -> None:
    """Execute example query against the document collection.

    Demonstrates how to use the query functionality with example parameters
    and prints the results in a readable format.
    """
    # Example query
    query = "What are the requirements for employee termination?"
    results = query_documents(
        query_text=query,
        n_results=3,
        min_similarity=0.7,  # Only return fairly similar results
    )

    # Print results
    print(f"\nQuery: {query}\n")
    for result in results:
        print(f"Rank {result['rank']} (Similarity: {result['similarity']:.2%})")
        print(f"Source: {result['metadata']['source']}")
        print(f"Chunk: {result['chunk'][:200]}...")  # Show first 200 chars
        print()


if __name__ == "__main__":
    main()
