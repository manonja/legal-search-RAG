#!/bin/bash

# Script to lock dependencies using uv

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

# Use highest resolution mode
echo "Using highest resolution mode for dependencies..."
uv pip compile pyproject.toml --resolution=highest -o requirements-lock.txt

echo "Dependencies locked successfully in requirements-lock.txt"
