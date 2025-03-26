#!/bin/bash

# Colors for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}   Legal Search RAG - Local Development Setup     ${NC}"
echo -e "${BLUE}==================================================${NC}"
echo ""

# Get script directory
SCRIPT_DIR=$(dirname "$(realpath "$0" 2>/dev/null || readlink -f "$0" 2>/dev/null || echo "$0")")
PROJECT_DIR=$(dirname "$SCRIPT_DIR")

# Change to project directory
cd "$PROJECT_DIR"

# Step 1: Check prerequisites
echo -e "${BLUE}Step 1: Checking prerequisites...${NC}"

if ! command -v pixi &> /dev/null; then
    echo -e "${RED}Error: Pixi is not installed. Please install Pixi first.${NC}"
    echo -e "${YELLOW}Visit https://pixi.sh for installation instructions.${NC}"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo -e "${RED}Error: npm is not installed. Please install Node.js first.${NC}"
    echo -e "${YELLOW}Visit https://nodejs.org for installation instructions.${NC}"
    exit 1
fi

echo -e "${GREEN}All prerequisites are met.${NC}"
echo ""

# Step 2: Setup API environment
echo -e "${BLUE}Step 2: Setting up API environment...${NC}"
echo ""

# Check if .env file exists
if [ ! -f "api/.env" ]; then
    echo -e "${YELLOW}Creating .env file from template...${NC}"
    cp api/.env.example api/.env
    echo -e "${GREEN}Created api/.env file. Please edit it to add your API keys.${NC}"
    echo -e "${YELLOW}Press Enter to open the file for editing...${NC}"
    read
    if command -v open &> /dev/null; then
        open api/.env
    else
        ${EDITOR:-nano} api/.env
    fi
else
    echo -e "${GREEN}Using existing api/.env file.${NC}"
fi

# Step a: Create directories
echo -e "${BLUE}Step 3: Creating document directories...${NC}"

# Extract directories from .env file
INPUT_DIR=$(grep "INPUT_DIR=" api/.env | cut -d= -f2 | sed 's/^~/'"$HOME"'/' | sed 's/"//g')
OUTPUT_DIR=$(grep "OUTPUT_DIR=" api/.env | cut -d= -f2 | sed 's/^~/'"$HOME"'/' | sed 's/"//g')
CHUNKS_DIR=$(grep "CHUNKS_DIR=" api/.env | cut -d= -f2 | sed 's/^~/'"$HOME"'/' | sed 's/"//g')
CHROMA_DIR=$(grep "CHROMA_DATA_DIR=" api/.env | cut -d= -f2 | sed 's/^~/'"$HOME"'/' | sed 's/"//g')

# Create directories
mkdir -p "$INPUT_DIR"
mkdir -p "$OUTPUT_DIR"
mkdir -p "$CHUNKS_DIR"
mkdir -p "$CHROMA_DIR"

echo -e "${GREEN}Created document directories:${NC}"
echo -e "  Input:    ${YELLOW}$INPUT_DIR${NC}"
echo -e "  Output:   ${YELLOW}$OUTPUT_DIR${NC}"
echo -e "  Chunks:   ${YELLOW}$CHUNKS_DIR${NC}"
echo -e "  ChromaDB: ${YELLOW}$CHROMA_DIR${NC}"
echo ""

# Step 4: Install dependencies
echo -e "${BLUE}Step 4: Installing dependencies...${NC}"
echo ""

# Change to API directory and install dependencies
cd "$PROJECT_DIR/api"
echo -e "${YELLOW}Installing API dependencies with Pixi...${NC}"
pixi install

# Change to frontend directory and install dependencies
cd "$PROJECT_DIR/frontend"
echo -e "${YELLOW}Installing frontend dependencies with npm...${NC}"
npm install

echo -e "${GREEN}Dependencies installed successfully.${NC}"
echo ""

# Step 5: Document processing instructions
echo -e "${BLUE}Step 5: Document processing workflow${NC}"
echo ""
echo -e "${YELLOW}Please follow these steps to process your legal documents:${NC}"
echo ""
echo -e "1. Copy your PDF or DOCX legal documents to: ${GREEN}$INPUT_DIR${NC}"
echo -e "2. Process documents with: ${GREEN}cd $PROJECT_DIR && pixi run process-docs${NC}"
echo -e "3. Chunk documents with: ${GREEN}cd $PROJECT_DIR && pixi run chunk-docs${NC}"
echo -e "4. Generate embeddings with: ${GREEN}cd $PROJECT_DIR && pixi run embed-docs${NC}"
echo ""

# Ask if user wants to add sample documents
read -p "Would you like to add sample documents? (y/n): " add_samples
if [[ $add_samples =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Sorry, sample document feature is not yet implemented.${NC}"
    echo -e "${YELLOW}Please add your own PDF or DOCX files to: ${GREEN}$INPUT_DIR${NC}"
fi

# Step 6: Starting the services
echo -e "${BLUE}Step 6: Starting the services${NC}"
echo ""
echo -e "${YELLOW}To start the API server:${NC}"
echo -e "  ${GREEN}cd $PROJECT_DIR && pixi run serve-api${NC}"
echo ""
echo -e "${YELLOW}To start the frontend:${NC}"
echo -e "  ${GREEN}cd $PROJECT_DIR/frontend && npm run dev${NC}"
echo ""
echo -e "${YELLOW}Access your application at:${NC}"
echo -e "  Frontend: ${GREEN}http://localhost:3000${NC}"
echo -e "  API: ${GREEN}http://localhost:8000/docs${NC}"
echo ""

echo -e "${BLUE}==================================================${NC}"
echo -e "${GREEN}Setup complete! You're ready to start developing.${NC}"
echo -e "${BLUE}==================================================${NC}"
