"""Base chunker class.

This module defines the base class for text chunkers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class Chunker(ABC):
    """Base class for text chunkers."""

    @abstractmethod
    def chunk(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Split text into chunks.

        Args:
            text: Text to split into chunks
            metadata: Document metadata to include with chunks

        Returns:
            List of dictionaries containing text chunks and metadata
        """
        pass
