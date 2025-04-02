"""Legal Search RAG Application.

This package contains the FastAPI application for legal document search.
"""

import os
from pathlib import Path

# Read version from VERSION file
version_file = Path(os.path.dirname(os.path.dirname(__file__))) / "VERSION"
with open(version_file, "r") as f:
    __version__ = f.read().strip()
