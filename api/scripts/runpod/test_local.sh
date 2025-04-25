#!/bin/bash
# Test the Mixtral handler locally

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(cd "$SCRIPT_DIR" && cd ../.. && pwd)"

# Create a testing environment with uv
if [ ! -d "$SCRIPT_DIR/test_env" ]; then
  echo "Creating test environment..."
  cd "$SCRIPT_DIR"

  # Check if uv is available
  if command -v uv &> /dev/null; then
    uv venv test_env --python=python3
    uv pip install -r requirements.txt --python test_env/bin/python --no-cache
    uv pip install torch --python test_env/bin/python --no-cache
  else
    # Fallback to using regular venv and pip
    echo "uv not found, falling back to standard venv and pip..."
    python3 -m venv test_env
    source test_env/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install torch
  fi
  echo "Test environment created successfully."
fi

# Activate the environment
if [[ "$OSTYPE" == "darwin"* ]] || [[ "$OSTYPE" == "linux-gnu"* ]]; then
  # macOS or Linux
  source "$SCRIPT_DIR/test_env/bin/activate"
else
  # Windows
  source "$SCRIPT_DIR/test_env/Scripts/activate"
fi

# Use a smaller model for local testing unless large model is specified
if [ -z "$MODEL_ID" ]; then
  export MODEL_ID="mistralai/Mistral-7B-Instruct-v0.2"
  echo "Using smaller model for local testing: $MODEL_ID"
  echo "Set MODEL_ID environment variable to override."
fi

# Set quantization to 4-bit for local testing unless specified
if [ -z "$QUANTIZATION" ]; then
  export QUANTIZATION="4bit"
  echo "Using 4-bit quantization for local testing."
  echo "Set QUANTIZATION environment variable to override."
fi

# Run the test with a simple prompt
cd "$SCRIPT_DIR"

if [ $# -eq 0 ]; then
  # No arguments provided, run with default prompt
  python test_handler.py --prompt "What are the key elements of a contract?" \
    --system-message "You are a helpful legal assistant. Keep answers brief."
else
  # Pass all arguments to the test handler
  python test_handler.py "$@"
fi
