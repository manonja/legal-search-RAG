#!/bin/bash

# Colors for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}   Legal Search RAG - Docker Compose Setup       ${NC}"
echo -e "${BLUE}==================================================${NC}"
echo ""

# Get script directory
SCRIPT_DIR=$(dirname "$(realpath "$0" 2>/dev/null || readlink -f "$0" 2>/dev/null || echo "$0")")
PROJECT_DIR=$(dirname "$SCRIPT_DIR")

# Change to project directory
cd "$PROJECT_DIR"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed. Please install Docker first.${NC}"
    echo -e "${YELLOW}Visit https://docs.docker.com/get-docker/ for installation instructions.${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed. Please install Docker Compose first.${NC}"
    echo -e "${YELLOW}Visit https://docs.docker.com/compose/install/ for installation instructions.${NC}"
    exit 1
fi

# Step 1: Setup API environment
echo -e "${BLUE}Step 1: Setting up API environment...${NC}"
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

# Step 2: Create directories
echo -e "${BLUE}Step 2: Creating document directories...${NC}"

# Extract directories from .env file - fixing sed pattern
if [ -f "api/.env" ]; then
    DATA_ROOT=$(grep "DATA_ROOT=" api/.env | cut -d= -f2 | tr -d '"' | sed "s|~|$HOME|g")

    # If DATA_ROOT is empty or not found, use a default
    if [ -z "$DATA_ROOT" ]; then
        DATA_ROOT="$HOME/legal-search-data"
    fi

    # Set directories based on DATA_ROOT
    INPUT_DIR="$DATA_ROOT/input"
    OUTPUT_DIR="$DATA_ROOT/processed"
    CHUNKS_DIR="$DATA_ROOT/chunks"
    CHROMA_DIR="$DATA_ROOT/chroma"

    # Also get values directly if they're set explicitly
    ENV_INPUT_DIR=$(grep "INPUT_DIR=" api/.env | cut -d= -f2 | tr -d '"' | sed "s|~|$HOME|g")
    ENV_OUTPUT_DIR=$(grep "OUTPUT_DIR=" api/.env | cut -d= -f2 | tr -d '"' | sed "s|~|$HOME|g")
    ENV_CHUNKS_DIR=$(grep "CHUNKS_DIR=" api/.env | cut -d= -f2 | tr -d '"' | sed "s|~|$HOME|g")
    ENV_CHROMA_DIR=$(grep "CHROMA_DATA_DIR=" api/.env | cut -d= -f2 | tr -d '"' | sed "s|~|$HOME|g")

    # Use explicit values if set
    [ -n "$ENV_INPUT_DIR" ] && INPUT_DIR="$ENV_INPUT_DIR"
    [ -n "$ENV_OUTPUT_DIR" ] && OUTPUT_DIR="$ENV_OUTPUT_DIR"
    [ -n "$ENV_CHUNKS_DIR" ] && CHUNKS_DIR="$ENV_CHUNKS_DIR"
    [ -n "$ENV_CHROMA_DIR" ] && CHROMA_DIR="$ENV_CHROMA_DIR"
else
    echo -e "${RED}Error: api/.env file not found.${NC}"
    exit 1
fi

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

# Step 3: Setup frontend environment file
echo -e "${BLUE}Step 3: Setting up frontend environment...${NC}"

# Create .env.local file in frontend directory
mkdir -p frontend
cat > frontend/.env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8001
EOF

echo -e "${GREEN}Created frontend/.env.local file.${NC}"
echo ""

# Step 4: Build and start Docker Compose
echo -e "${BLUE}Step 4: Building and starting Docker Compose...${NC}"
echo ""

echo -e "${YELLOW}Building Docker images...${NC}"
# Define environment variables for docker-compose
export API_PORT=8001
export FRONTEND_PORT=3000
export TENANT_ID=default
export ENV_FILE=../api/.env

echo -e "${YELLOW}Starting Docker containers...${NC}"
docker compose -f shared/docker-compose.yml up -d

echo -e "${GREEN}Docker containers are now running!${NC}"
echo ""
echo -e "${YELLOW}To view the logs, run:${NC}"
echo -e "  ${GREEN}docker compose -f shared/docker-compose.yml logs -f${NC}"
echo ""
echo -e "${YELLOW}To stop the containers, run:${NC}"
echo -e "  ${GREEN}docker compose -f shared/docker-compose.yml down${NC}"
echo ""
echo -e "${YELLOW}Access your application at:${NC}"
echo -e "  Frontend: ${GREEN}http://localhost:3000${NC}"
echo -e "  API: ${GREEN}http://localhost:8001/docs${NC}"
echo ""

echo -e "${BLUE}==================================================${NC}"
echo -e "${GREEN}Setup complete! The application is now running.${NC}"
echo -e "${BLUE}==================================================${NC}"
