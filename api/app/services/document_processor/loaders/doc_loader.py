"""DOC document loader.

This module provides functionality to extract text from DOC documents using antiword.
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, Any

from app.core.struct_logger import log
from app.services.document_processor.loaders.loader_base import DocumentLoader


class DOCLoader(DocumentLoader):
    """Loader for DOC documents using antiword."""

    def load(self, file_path: Path) -> tuple[str, Dict[str, Any]]:
        """Extract text from a DOC file.

        Args:
            file_path: Path to the DOC file

        Returns:
            Tuple containing extracted text and document metadata
        """
        text = ""
        metadata = {"original_file_type": "doc"}

        try:
            # Validate the file path to ensure it exists and is a file
            if not file_path.is_file():
                raise ValueError(f"File not found: {file_path}")

            # Verify file extension is .doc
            if not str(file_path).lower().endswith(".doc"):
                raise ValueError(f"File does not have .doc extension: {file_path}")

            # Additional validation - check file size is reasonable (prevent huge files)
            file_size = file_path.stat().st_size
            if file_size > 50 * 1024 * 1024:  # 50 MB limit
                raise ValueError(f"File too large to process: {file_size} bytes")

            metadata["file_size_bytes"] = file_size

            # Get the full path to antiword executable
            antiword_path = "/usr/bin/antiword"  # Default path on Linux/Docker
            if not os.path.exists(antiword_path):
                # Try macOS Homebrew location
                antiword_path = "/usr/local/bin/antiword"
                if not os.path.exists(antiword_path):
                    # Last resort, use PATH resolution
                    antiword_path = "antiword"

            # Call antiword as a subprocess with validated inputs
            result = subprocess.run(  # noqa: S603
                [antiword_path, str(file_path)],
                capture_output=True,
                text=True,
                check=True,
            )
            text = result.stdout

        except subprocess.CalledProcessError as e:
            log.error("Error running antiword", file_path=str(file_path), error=str(e))
            raise ValueError(f"Failed to extract text with antiword: {str(e)}") from e
        except Exception as e:
            log.error("Error extracting DOC", file_path=str(file_path), error=str(e))
            raise ValueError(f"Failed to extract text from DOC: {str(e)}") from e

        return text, metadata
