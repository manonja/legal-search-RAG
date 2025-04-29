"""
Shared pytest fixtures for all test modules.
"""

import os
import shutil
import tempfile
from pathlib import Path

import pytest

from app.core.config import get_settings


@pytest.fixture(scope="module")
def test_settings_module():
    """Create test settings with a temporary data directory, with module scope."""
    settings = get_settings()
    temp_dir = tempfile.mkdtemp(prefix="test_datastore_")
    settings.DATA_DIR = Path(temp_dir)

    # Yield settings for use in tests
    yield settings

    # Clean up temp directory after tests
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)


@pytest.fixture
def test_settings():
    """Create test settings with a temporary data directory, with function scope."""
    settings = get_settings()
    temp_dir = tempfile.mkdtemp(prefix="test_datastore_")
    settings.DATA_DIR = Path(temp_dir)

    # Yield settings for use in tests
    yield settings

    # Clean up temp directory after tests
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
