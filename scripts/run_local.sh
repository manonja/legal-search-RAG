#!/bin/bash

# Colors for output formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}Legal Search RAG - Local Development${NC}"
echo "======================================"

# First ensure directory structure is set up correctly
if [ -f "$SCRIPT_DIR/setup_dirs.sh" ]; then
    echo -e "${BLUE}Ensuring directory structure is set up...${NC}"
    bash "$SCRIPT_DIR/setup_dirs.sh"
else
    echo -e "${RED}Error: setup_dirs.sh script not found${NC}"
    exit 1
fi

# Check for port availability
check_port() {
    local port=$1
    if command -v lsof >/dev/null 2>&1; then
        if lsof -i :"$port" >/dev/null 2>&1; then
            return 1 # Port is in use
        else
            return 0 # Port is available
        fi
    else
        # If lsof is not available, try nc
        if command -v nc >/dev/null 2>&1; then
            nc -z localhost "$port" >/dev/null 2>&1
            if [ $? -eq 0 ]; then
                return 1 # Port is in use
            else
                return 0 # Port is available
            fi
        fi
    fi

    # If we can't check, assume it's available
    return 0
}

# Check for the .env file
if [ ! -f "$PROJECT_DIR/api/.env" ]; then
    echo -e "${RED}Error: .env file not found at $PROJECT_DIR/api/.env${NC}"
    echo -e "${YELLOW}Please run the local_setup.sh script first to set up the environment.${NC}"
    exit 1
fi

# Define a function to expand home directory and environment variables
expand_path() {
    eval echo "$1"
}

# Extract settings from .env file
API_PORT=$(grep "API_PORT" "$PROJECT_DIR/api/.env" | cut -d '=' -f2 | sed 's/"//g' | sed "s/'//g")
DATA_ROOT=$(grep "DATA_ROOT=" "$PROJECT_DIR/api/.env" | cut -d '=' -f2 | sed 's/"//g' | sed "s/'//g")
DATA_ROOT=$(expand_path "$DATA_ROOT")
INPUT_DIR=$(grep "INPUT_DIR=" "$PROJECT_DIR/api/.env" | cut -d '=' -f2- | sed 's/"//g' | sed "s/'//g")
INPUT_DIR=$(expand_path "$INPUT_DIR")

# Default port if not found
API_PORT=${API_PORT:-8000}

# Check if API port is available
if ! check_port "$API_PORT"; then
    echo -e "${RED}Error: Port $API_PORT is already in use.${NC}"
    echo -e "${YELLOW}Please either:${NC}"
    echo "  1. Close the application using this port"
    echo "  2. Change the API_PORT in api/.env to a different value"
    exit 1
fi

# Check if there are documents to process
echo -e "${BLUE}Checking for documents to process...${NC}"
if [ -z "$(find "$INPUT_DIR" -type f \( -name "*.pdf" -o -name "*.docx" \) 2>/dev/null)" ]; then
    echo -e "${YELLOW}No documents found in $INPUT_DIR${NC}"
    echo "Please add PDF or DOCX files to process them automatically."
    echo -e "${YELLOW}You can add documents to: ${NC}$INPUT_DIR"
else
    echo -e "${GREEN}Found documents in $INPUT_DIR${NC}"
    read -p "Would you like to process them now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}Processing documents...${NC}"
        cd "$PROJECT_DIR" && pixi run process-docs

        echo -e "${BLUE}Chunking documents...${NC}"
        cd "$PROJECT_DIR" && pixi run chunk-docs

        echo -e "${BLUE}Generating embeddings...${NC}"
        cd "$PROJECT_DIR" && pixi run embed-docs
    fi
fi

echo -e "${BLUE}Starting API server on http://localhost:$API_PORT${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
cd "$PROJECT_DIR" && pixi run serve-api
