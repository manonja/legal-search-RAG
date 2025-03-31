#!/bin/bash

# Script to lock dependencies using uv native lock

echo "Locking dependencies using uv..."

# Get Python version
PYTHON_VERSION=$(python -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "Using Python $PYTHON_VERSION"

# Check Python version
if [[ "$PYTHON_VERSION" == "3.12" ]]; then
    echo "Warning: Python 3.12 is not officially supported by this project."
    echo "Please downgrade to Python 3.11 for full compatibility with all dependencies."
    echo "Installation may fail or behave unexpectedly with Python 3.12."
fi

# Use uv lock to generate uv.lock with all extras
echo "Generating uv.lock from pyproject.toml..."
uv lock --upgrade  --verbose

# Verify lock file was generated
if [ ! -f "uv.lock" ]; then
    echo "Error: Failed to generate uv.lock file."
    exit 1
fi

echo "Dependencies locked successfully in uv.lock"
