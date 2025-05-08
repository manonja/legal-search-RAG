"""SemChunk chunker.

This module provides text chunking using the semchunk library.
"""

import semchunk
import tiktoken
from typing import List, Dict, Any, Callable

from app.core.config import get_settings
from app.core.struct_logger import log
from app.services.document_processor.chunkers.chunker_base import Chunker


class SemChunkChunker(Chunker):
    """Text chunker using the semchunk library."""

    def __init__(
        self,
        tokenizer_name: str = None,
        chunk_size: int = None,
        overlap: int = None,
        token_counter: Callable[[str], int] = None,
    ):
        """Initialize the SemChunk chunker.

        Args:
            tokenizer_name: Name of the tokenizer to use
            chunk_size: Maximum number of tokens per chunk
            overlap: Number of tokens to overlap between chunks
            token_counter: Custom token counting function (if provided)
        """
        settings = get_settings()
        self.tokenizer_name = tokenizer_name or settings.SEMCHUNK_TOKENIZER
        self.chunk_size = chunk_size or settings.SEMCHUNK_CHUNK_SIZE
        self.overlap = overlap or settings.SEMCHUNK_OVERLAP_TOKENS

        # Initialize tokenizer and counter
        if token_counter:
            self.token_counter = token_counter
        else:
            try:
                tokenizer = tiktoken.get_encoding(self.tokenizer_name)
                self.token_counter = lambda text: len(tokenizer.encode(text))
            except Exception as e:
                log.error(
                    "Failed to initialize tokenizer",
                    tokenizer=self.tokenizer_name,
                    error=str(e),
                )
                raise ValueError(
                    f"Failed to initialize tokenizer {self.tokenizer_name}: {str(e)}"
                ) from e

        # Initialize the chunker function
        try:
            self.chunker = semchunk.chunkerify(
                tokenizer_or_token_counter=self.token_counter,
                chunk_size=self.chunk_size,
            )
        except Exception as e:
            log.error(
                "Failed to initialize semchunk chunker",
                tokenizer=self.tokenizer_name,
                error=str(e),
            )
            raise ValueError(f"Failed to initialize semchunk chunker: {str(e)}") from e

    def chunk(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Split text into chunks using semchunk.

        Args:
            text: Text to split into chunks
            metadata: Document metadata to include with chunks

        Returns:
            List of dictionaries containing text chunks and metadata
        """
        try:
            # Check for empty text
            if not text or not text.strip():
                log.warning(
                    "Empty text provided for chunking",
                    document_id=metadata.get("document_id", "unknown"),
                )
                return []

            # Apply chunking
            text_chunks = self.chunker(text, overlap=self.overlap)

            if not text_chunks:
                log.warning(
                    "Semchunk produced no chunks for document",
                    document_id=metadata.get("document_id", "unknown"),
                )
                return []

            # Process chunks into result format with metadata
            result = []
            for i, chunk_text in enumerate(text_chunks, 1):
                # Count tokens in the chunk
                token_count = self.token_counter(chunk_text)

                # Create chunk object with metadata
                chunk = {
                    "text": chunk_text,
                    "metadata": {**metadata, "chunk_index": i},
                    "token_count": token_count,
                }
                result.append(chunk)

            log.info(
                "Document chunked successfully",
                document_id=metadata.get("document_id", "unknown"),
                chunk_count=len(result),
            )
            return result

        except Exception as e:
            log.error(
                "Error during text chunking",
                document_id=metadata.get("document_id", "unknown"),
                error=str(e),
            )
            raise ValueError(f"Failed to chunk document text: {str(e)}") from e
