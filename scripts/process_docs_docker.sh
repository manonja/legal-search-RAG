#!/bin/bash

# Colors for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}   Legal Search RAG - Process Documents in Docker ${NC}"
echo -e "${BLUE}==================================================${NC}"
echo ""

# Get script directory
SCRIPT_DIR=$(dirname "$(realpath "$0" 2>/dev/null || readlink -f "$0" 2>/dev/null || echo "$0")")
PROJECT_DIR=$(dirname "$SCRIPT_DIR")

# Change to project directory
cd "$PROJECT_DIR"

# Default tenant
TENANT_ID=default

# Check if Docker container is running
if ! docker ps | grep -q "legal-search-api-$TENANT_ID"; then
    echo -e "${RED}Error: Docker container is not running. Please start it with scripts/run_with_docker.sh first.${NC}"
    exit 1
fi

# Get INPUT_DIR from .env file
if [ -f "api/.env" ]; then
    INPUT_DIR=$(grep "INPUT_DIR=" api/.env | cut -d= -f2 | sed 's/^~/'"$HOME"'/' | sed 's/"//g')
else
    echo -e "${RED}Error: api/.env file not found. Please run scripts/run_with_docker.sh first.${NC}"
    exit 1
fi

# Prompt user to copy documents if none exist
if [ -z "$(ls -A "$INPUT_DIR" 2>/dev/null)" ]; then
    echo -e "${YELLOW}No documents found in $INPUT_DIR${NC}"
    echo -e "${YELLOW}Please copy your PDF or DOCX legal documents to that directory.${NC}"

    read -p "Would you like to open the input directory? (y/n): " open_dir
    if [[ $open_dir =~ ^[Yy]$ ]]; then
        if command -v open &> /dev/null; then
            open "$INPUT_DIR"
        elif command -v xdg-open &> /dev/null; then
            xdg-open "$INPUT_DIR"
        elif command -v explorer &> /dev/null; then
            explorer "$INPUT_DIR"
        else
            echo -e "${YELLOW}Manual path: $INPUT_DIR${NC}"
        fi
    fi

    read -p "Continue once you've added documents? (y/n): " continue_process
    if [[ ! $continue_process =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Exiting without processing documents.${NC}"
        exit 0
    fi
fi

# Process documents
echo -e "${BLUE}Processing documents...${NC}"
docker exec legal-search-api-$TENANT_ID python process_docs.py
if [ $? -ne 0 ]; then
    echo -e "${RED}Error during document processing!${NC}"
    exit 1
fi

echo -e "${GREEN}Document processing complete.${NC}"

# Chunk documents
echo -e "${BLUE}Chunking documents...${NC}"
docker exec legal-search-api-$TENANT_ID python chunk.py
if [ $? -ne 0 ]; then
    echo -e "${RED}Error during document chunking!${NC}"
    exit 1
fi

echo -e "${GREEN}Document chunking complete.${NC}"

# Embed documents
echo -e "${BLUE}Generating embeddings...${NC}"
docker exec legal-search-api-$TENANT_ID python embeddings.py
if [ $? -ne 0 ]; then
    echo -e "${RED}Error during embedding generation!${NC}"
    exit 1
fi

echo -e "${GREEN}Embedding generation complete.${NC}"

echo -e "${BLUE}==================================================${NC}"
echo -e "${GREEN}All documents processed successfully!${NC}"
echo -e "${BLUE}==================================================${NC}"
echo ""
echo -e "${YELLOW}You can now search your documents at:${NC}"
echo -e "  ${GREEN}http://localhost:3000${NC}"
