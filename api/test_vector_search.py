#!/usr/bin/env python3
"""Test script for vector search functionality."""

import asyncio
import logging
import sys

from app.services.database.vector_service import vector_service
from app.services.database.database import get_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)


async def test_vector_search():
    """Test vector search functionality with a simple query."""
    try:
        # Create a database session
        db = next(get_db())

        # Test query
        query = "Is the right to a healthy environment constitutionalized?"

        # Log the test
        print(f"\nTesting vector search with query: '{query}'")

        # Run the search
        result = await vector_service.vector_search(
            db=db,
            query_text=query,
            limit=5,
            min_score=0.7,
            context_window=1,
            include_document_metadata=False,
        )

        # Print result summary
        if isinstance(result, list):
            print(f"Search returned {len(result)} results")
            if result:
                print(f"First result: {result[0]['content'][:100]}...")
        else:
            print(f"Search returned {result.get('total_results', 0)} results")
            if result.get("results"):
                print(
                    f"First result: {result['results'][0]['chunk']['content'][:100]}..."
                )

        print("\nTest completed successfully")

    except Exception as e:
        print(f"Error during test: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_vector_search())
