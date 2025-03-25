#!/usr/bin/env python3

"""

Test script for the Legal Search RAG system.

Provides a command-line interface for querying legal documents.

"""

import argparse

from query import query_documents


def format_result(result: dict) -> str:
    """Format a single search result for display."""
    output = [
        f"\n=== Result {result['rank']} (Similarity: {result['similarity']:.2%}) ===",
        f"Source: {result['metadata']['source']}",
        f"Context: {result['chunk']}",
        "=" * 80,
    ]
    return "\n".join(output)


def search_legal_docs(
    query: str,
    num_results: int = 5,
    min_similarity: float = 0.0,
) -> None:
    """
    Search legal documents and display results.

    Args:
        query: The search query
        num_results: Number of results to return
        min_similarity: Minimum similarity threshold (0 to 1)
    """
    print(f"\nSearching for: {query}")
    print(f"Parameters: num_results={num_results}, min_similarity={min_similarity}")
    print("\nRetrieving results...")

    results = query_documents(
        query_text=query,
        n_results=num_results,
        min_similarity=min_similarity,
    )

    if not results:
        print("\nNo results found matching your query.")
        return

    for result in results:
        print(format_result(result))


def main() -> None:
    """Run the test script."""
    parser = argparse.ArgumentParser(
        description="Test the Legal Search RAG system with custom queries."
    )
    parser.add_argument(
        "query",
        nargs="?",  # Make positional argument optional
        help="The search query (if not provided, will prompt for input)",
    )
    parser.add_argument(
        "-n",
        "--num-results",
        type=int,
        default=5,
        help="Number of results to return (default: 5)",
    )
    parser.add_argument(
        "-s",
        "--min-similarity",
        type=float,
        default=0.0,
        help="Minimum similarity threshold, 0 to 1 (default: 0.0)",
    )

    args = parser.parse_args()

    # If no query provided as argument, enter interactive mode
    if not args.query:
        print("\nLegal Search RAG System - Interactive Mode")
        print("Enter 'quit' or 'exit' to end the session")

        while True:
            query = input("\nEnter your legal query: ").strip()
            if query.lower() in ("quit", "exit"):
                break
            if query:
                search_legal_docs(
                    query=query,
                    num_results=args.num_results,
                    min_similarity=args.min_similarity,
                )
    else:
        # Single query mode
        search_legal_docs(
            query=args.query,
            num_results=args.num_results,
            min_similarity=args.min_similarity,
        )


if __name__ == "__main__":
    main()
