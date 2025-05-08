"""Base preprocessor class.

This module defines the base class for text preprocessors.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class Preprocessor(ABC):
    """Base class for text preprocessors."""

    @abstractmethod
    def preprocess(self, text: str, metadata: Dict[str, Any]) -> str:
        """Clean and normalize text.

        Args:
            text: Text to preprocess
            metadata: Document metadata (may be updated by the preprocessor)

        Returns:
            Preprocessed text
        """
        pass
