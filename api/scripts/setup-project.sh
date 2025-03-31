#!/bin/bash

# Script to set up the project with uv

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "uv is not installed. Installing now..."
    curl -sSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Lock dependencies
echo "Locking dependencies..."
uv pip compile pyproject.toml --resolution=highest -o requirements-lock.txt

# Create a virtual environment
echo "Creating virtual environment..."
uv venv

# Install dependencies
echo "Installing dependencies..."
source .venv/bin/activate
uv pip install -e ".[dev]"

echo "Project setup complete!"
echo "Activate the virtual environment with: source .venv/bin/activate"
