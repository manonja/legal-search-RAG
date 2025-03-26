#!/bin/bash

# Colors for better output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=======================================${NC}"
echo -e "${BLUE}  Legal Search RAG - Directory Setup  ${NC}"
echo -e "${BLUE}=======================================${NC}"

# Get the script directory and project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Load environment variables
ENV_FILE="$PROJECT_ROOT/api/.env"

# Check if the environment file exists
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: Environment file not found at $ENV_FILE${NC}"
    echo -e "${YELLOW}Please create the .env file by copying from .env.example${NC}"
    exit 1
fi

# Define a function to expand home directory and environment variables
expand_path() {
    eval echo "$1"
}

# Extract and expand directory paths from .env
DATA_ROOT=$(grep "DATA_ROOT=" "$ENV_FILE" | cut -d '=' -f2 | sed 's/"//g' | sed "s/'//g")
DATA_ROOT=$(expand_path "$DATA_ROOT")

INPUT_DIR=$(grep "INPUT_DIR=" "$ENV_FILE" | cut -d '=' -f2- | sed 's/"//g' | sed "s/'//g")
INPUT_DIR=$(expand_path "$INPUT_DIR")

OUTPUT_DIR=$(grep "OUTPUT_DIR=" "$ENV_FILE" | cut -d '=' -f2- | sed 's/"//g' | sed "s/'//g")
OUTPUT_DIR=$(expand_path "$OUTPUT_DIR")

CHUNKS_DIR=$(grep "CHUNKS_DIR=" "$ENV_FILE" | cut -d '=' -f2- | sed 's/"//g' | sed "s/'//g")
CHUNKS_DIR=$(expand_path "$CHUNKS_DIR")

CHROMA_DIR=$(grep "CHROMA_DATA_DIR=" "$ENV_FILE" | cut -d '=' -f2- | sed 's/"//g' | sed "s/'//g")
CHROMA_DIR=$(expand_path "$CHROMA_DIR")

# Legacy paths (for backward compatibility)
LEGACY_INPUT_DIR="$HOME/Downloads/legaldocs_input"
LEGACY_OUTPUT_DIR="$HOME/Downloads/legaldocs_processed"
LEGACY_CHUNKS_DIR="$HOME/Downloads/legaldocs_chunks"
LEGACY_CHROMA_DIR="$HOME/Downloads/legal_chroma"

# Create directories
echo -e "${BLUE}Creating directory structure...${NC}"
mkdir -p "$DATA_ROOT"
mkdir -p "$INPUT_DIR"
mkdir -p "$OUTPUT_DIR"
mkdir -p "$CHUNKS_DIR"
mkdir -p "$CHROMA_DIR"

echo -e "${GREEN}✓ Created base data directory: ${NC}$DATA_ROOT"
echo -e "${GREEN}✓ Created input directory: ${NC}$INPUT_DIR"
echo -e "${GREEN}✓ Created output directory: ${NC}$OUTPUT_DIR"
echo -e "${GREEN}✓ Created chunks directory: ${NC}$CHUNKS_DIR"
echo -e "${GREEN}✓ Created ChromaDB directory: ${NC}$CHROMA_DIR"

# Create symlinks for backward compatibility if the paths are different
echo -e "${BLUE}Setting up backward compatibility...${NC}"

create_symlink() {
    local source="$1"
    local target="$2"

    # Check if the source and target are the same path
    if [ "$(realpath "$source")" = "$(realpath "$target")" ]; then
        echo -e "${YELLOW}• Skipping symlink for $source (same as target)${NC}"
        return
    fi

    # Check if target exists but is not a symlink
    if [ -e "$target" ] && [ ! -L "$target" ]; then
        # Target exists but is not a symlink, move contents
        echo -e "${YELLOW}• $target exists, moving contents to $source...${NC}"
        if [ -d "$target" ] && [ "$(ls -A "$target" 2>/dev/null)" ]; then
            cp -r "$target"/* "$source"/ 2>/dev/null
            rm -rf "$target"
        fi
    fi

    # Create symlink
    if [ ! -e "$target" ]; then
        ln -sf "$source" "$target"
        echo -e "${GREEN}✓ Created symlink: ${NC}$target -> $source"
    fi
}

create_symlink "$INPUT_DIR" "$LEGACY_INPUT_DIR"
create_symlink "$OUTPUT_DIR" "$LEGACY_OUTPUT_DIR"
create_symlink "$CHUNKS_DIR" "$LEGACY_CHUNKS_DIR"
create_symlink "$CHROMA_DIR" "$LEGACY_CHROMA_DIR"

echo -e "${BLUE}=======================================${NC}"
echo -e "${GREEN}Directory setup complete!${NC}"
echo -e "${YELLOW}You can now:${NC}"
echo -e "  1. Add PDF/DOCX files to ${BLUE}$INPUT_DIR${NC}"
echo -e "  2. Process documents with ${BLUE}pixi run process-docs${NC}"
echo -e "  3. Run the API with ${BLUE}pixi run serve-api${NC}"
echo -e "${BLUE}=======================================${NC}"
