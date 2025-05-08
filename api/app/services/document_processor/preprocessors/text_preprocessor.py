"""Text preprocessor.

This module provides basic text cleaning and normalization.
"""

import re
from typing import Dict, Any

from app.core.struct_logger import log
from app.services.document_processor.preprocessors.preprocessor_base import Preprocessor


class TextPreprocessor(Preprocessor):
    """Basic text preprocessor for cleaning and normalizing text."""

    def preprocess(self, text: str, metadata: Dict[str, Any]) -> str:
        """Clean and normalize text.

        Args:
            text: Text to preprocess
            metadata: Document metadata

        Returns:
            Preprocessed text
        """
        try:
            if not text:
                return text

            # Store original character count in metadata
            metadata["original_char_count"] = len(text)

            # Replace multiple newlines with a single one
            text = re.sub(r"\n{3,}", "\n\n", text)

            # Replace multiple spaces with a single one
            text = re.sub(r" {2,}", " ", text)

            # Remove null bytes and other control characters
            text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)

            # Normalize whitespace
            text = text.strip()

            # Store processed character count in metadata
            metadata["processed_char_count"] = len(text)

            return text

        except Exception as e:
            log.error(
                "Error preprocessing text",
                document_id=metadata.get("document_id", "unknown"),
                error=str(e),
            )
            # Return original text in case of error
            return text
