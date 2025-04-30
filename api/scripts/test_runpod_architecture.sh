#!/bin/bash

# Testing script for RunPod architecture
# This script runs the tests focusing only on the RunPod implementation

set -e  # Exit on error

# Colors for terminal output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting RunPod Architecture Testing Plan${NC}"

# Setup virtual environment and sync dependencies
echo -e "${YELLOW}Setting up virtual environment and syncing dependencies...${NC}"
if ! command -v uv &> /dev/null; then
    echo -e "${RED}Error: 'uv' command not found. Please install uv package manager first.${NC}"
    echo -e "You can install it with: curl -sSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Create or update virtual environment
uv venv .venv

# Detect shell and use appropriate activation command
if [[ "$SHELL" == *"fish"* ]]; then
    # Fish shell - don't source directly, use eval
    eval "$(.venv/bin/python -c 'import os, sys; from pathlib import Path; p = Path(sys.prefix); print(f\"set -gx PATH {p}/bin $PATH; set -gx VIRTUAL_ENV {p}\")')"
elif [[ "$SHELL" == *"zsh"* ]]; then
    # Zsh shell
    source .venv/bin/activate
else
    # Bash or other shells
    source .venv/bin/activate
fi

# Sync dependencies
uv sync
echo -e "${GREEN}Virtual environment ready and dependencies synced${NC}"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}No .env file found. Creating one from the example...${NC}"
    cat > .env << EOL
# RunPod Configuration
RUNPOD_API_KEY=your_runpod_api_key
RUNPOD_MIXTRAL_ENDPOINT_ID=your_mixtral_endpoint_id
RUNPOD_EMBEDDING_ENDPOINT_ID=your_embedding_endpoint_id
HF_EMBEDDING_MODEL=nlpaueb/legal-bert-base-uncased
USE_RUNPOD=true

# ChromaDB Configuration
COLLECTION_NAME=legal_docs
CHROMA_DIR=./data/chroma

# API Authentication (for local testing)
API_TOKEN=test-token

# Other Settings
LOG_LEVEL=DEBUG
DEBUG=true
TESTING=false
EOL
    echo -e "${YELLOW}Please edit the .env file to add your RunPod API keys and endpoint IDs${NC}"
    exit 1
fi

# 1. Check required environment variables
echo -e "${YELLOW}Checking environment variables...${NC}"
missing_vars=0

# Check RunPod variables when USE_RUNPOD is true
if grep -q "USE_RUNPOD=true" .env; then
    if ! grep -q "RUNPOD_API_KEY=.*[a-zA-Z0-9]" .env; then
        echo -e "${RED}Missing RUNPOD_API_KEY in .env file${NC}"
        missing_vars=$((missing_vars+1))
    fi

    if ! grep -q "RUNPOD_MIXTRAL_ENDPOINT_ID=.*[a-zA-Z0-9]" .env; then
        echo -e "${RED}Missing RUNPOD_MIXTRAL_ENDPOINT_ID in .env file${NC}"
        missing_vars=$((missing_vars+1))
    fi

    if ! grep -q "RUNPOD_EMBEDDING_ENDPOINT_ID=.*[a-zA-Z0-9]" .env; then
        echo -e "${RED}Missing RUNPOD_EMBEDDING_ENDPOINT_ID in .env file${NC}"
        missing_vars=$((missing_vars+1))
    fi
fi

if [ $missing_vars -gt 0 ]; then
    echo -e "${RED}Please set the required environment variables in your .env file${NC}"
    exit 1
fi

echo -e "${GREEN}Environment variables check passed${NC}"

# 2. Check for test document
echo -e "${YELLOW}Checking for test document...${NC}"
TEST_DOC="tests/data/test_document.pdf"

if [ ! -f "$TEST_DOC" ]; then
    echo -e "${YELLOW}Test document not found at $TEST_DOC${NC}"
    echo -e "${YELLOW}Creating test data directory...${NC}"
    mkdir -p tests/data

    echo -e "${YELLOW}Creating a sample PDF for testing...${NC}"
    # Create a simple text file
    cat > tests/data/test_content.txt << EOL
This is a test legal document for testing the RunPod architecture.

Section 1: Introduction
This document outlines various legal provisions related to data privacy and security.

Section 2: Key Legal Provisions
2.1 All data must be encrypted at rest and in transit.
2.2 Personal data must be processed lawfully, fairly, and transparently.
2.3 Personal data must be collected for specified, explicit, and legitimate purposes.

Section 3: Compliance Requirements
Organizations must implement appropriate technical and organizational measures
to ensure a level of security appropriate to the risk.
EOL

    # Try to convert text to PDF if possible
    if command -v convert &> /dev/null; then
        convert -size 612x792 xc:white -font Helvetica -pointsize 12 -fill black \
            -annotate +36+36 "@tests/data/test_content.txt" \
            tests/data/test_document.pdf
        echo -e "${GREEN}Created test PDF document${NC}"
    elif command -v wkhtmltopdf &> /dev/null; then
        wkhtmltopdf tests/data/test_content.txt tests/data/test_document.pdf
        echo -e "${GREEN}Created test PDF document${NC}"
    else
        echo -e "${RED}Could not create a PDF test document. Please place a test document at $TEST_DOC${NC}"
        echo -e "${YELLOW}Alternatively, you can specify a test document with the --file parameter when running the test script${NC}"
        exit 1
    fi
fi

# 3. Start the API server in the background
echo -e "${YELLOW}Starting the API server...${NC}"
pkill -f "uvicorn app.main:app" || true  # Kill any existing uvicorn server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > api_server.log 2>&1 &
API_PID=$!

# Wait for server to start
echo -e "${YELLOW}Waiting for server to start...${NC}"
max_retries=10
retries=0
while ! curl -s http://localhost:8000/api/health > /dev/null && [ $retries -lt $max_retries ]; do
    sleep 2
    retries=$((retries+1))
    echo -e "${YELLOW}Waiting for server (attempt $retries/$max_retries)...${NC}"
done

if [ $retries -ge $max_retries ]; then
    echo -e "${RED}Server failed to start within expected time. Check logs in api_server.log${NC}"
    kill $API_PID
    exit 1
fi

echo -e "${GREEN}API server started on http://localhost:8000${NC}"

# 4. Run the test script
echo -e "${YELLOW}Running RunPod integration tests...${NC}"
python test_runpod_integration.py --verbose

# 5. Test shutdown
echo -e "${YELLOW}Shutting down API server...${NC}"
kill $API_PID

echo -e "${GREEN}All done! Check the test results above.${NC}"

# Cleanup function
function cleanup {
    echo -e "${YELLOW}Cleaning up...${NC}"
    pkill -f "uvicorn app.main:app" || true
}

# Register the cleanup function for script exit
trap cleanup EXIT
