#!/bin/bash

# Colors for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get tenant ID from command line or use default
TENANT_ID=${1:-"test1"}

echo -e "${BLUE}Processing documents for tenant: ${GREEN}$TENANT_ID${NC}"

# Check if container is running
if ! docker ps | grep -q "legal-search-api-$TENANT_ID"; then
    echo -e "${YELLOW}Container legal-search-api-$TENANT_ID is not running.${NC}"
    echo -e "${YELLOW}Please start the tenant first with ./scripts/deploy_tenant.sh${NC}"
    exit 1
fi

# Check if input directory has documents
INPUT_DIR="tenants/$TENANT_ID/docs/input"
if [ ! -d "$INPUT_DIR" ] || [ -z "$(ls -A $INPUT_DIR 2>/dev/null)" ]; then
    echo -e "${YELLOW}No documents found in $INPUT_DIR${NC}"
    echo -e "${YELLOW}Please add PDF or DOCX documents to this directory first.${NC}"
    exit 1
fi

echo -e "${BLUE}Found $(ls -1 $INPUT_DIR | wc -l | tr -d ' ') documents in input directory${NC}"

# Step 1: Process documents (convert to text)
echo -e "\n${BLUE}Step 1/3: Processing documents (extracting text)...${NC}"
docker exec legal-search-api-$TENANT_ID bash -c "source ~/.pixi/env && pixi run process-docs"

# Check if processing was successful
if [ $? -ne 0 ]; then
    echo -e "${RED}Document processing failed. Check the logs above for errors.${NC}"
    exit 1
fi

# Step 2: Chunk documents
echo -e "\n${BLUE}Step 2/3: Chunking documents...${NC}"
docker exec legal-search-api-$TENANT_ID bash -c "source ~/.pixi/env && pixi run chunk-docs"

# Check if chunking was successful
if [ $? -ne 0 ]; then
    echo -e "${RED}Document chunking failed. Check the logs above for errors.${NC}"
    exit 1
fi

# Step 3: Generate embeddings
echo -e "\n${BLUE}Step 3/3: Generating embeddings (this may take a while)...${NC}"
docker exec legal-search-api-$TENANT_ID bash -c "source ~/.pixi/env && pixi run embed-docs"

# Check if embedding generation was successful
if [ $? -ne 0 ]; then
    echo -e "${RED}Embedding generation failed. Check the logs above for errors.${NC}"
    exit 1
fi

# Check output directories
echo -e "\n${GREEN}Processing complete!${NC}"
echo -e "${BLUE}Processed document stats:${NC}"
echo -e "  Input files: $(ls -1 $INPUT_DIR | wc -l | tr -d ' ') files"
echo -e "  Processed text files: $(ls -1 tenants/$TENANT_ID/docs/output 2>/dev/null | wc -l | tr -d ' ') files"
echo -e "  Chunked files: $(ls -1 tenants/$TENANT_ID/docs/chunks 2>/dev/null | wc -l | tr -d ' ') files"

# Remind about API endpoints
API_PORT=$(grep "^API_PORT=" .env.$TENANT_ID 2>/dev/null | cut -d= -f2)
FRONTEND_PORT=$(grep "^FRONTEND_PORT=" .env.$TENANT_ID 2>/dev/null | cut -d= -f2)

echo -e "\n${BLUE}Your RAG system is ready for queries!${NC}"
echo -e "  API: ${GREEN}http://localhost:$API_PORT${NC}"
echo -e "  Frontend: ${GREEN}http://localhost:$FRONTEND_PORT${NC}"
echo -e "\n${BLUE}Example API query:${NC}"
echo -e "${GREEN}curl -X POST http://localhost:$API_PORT/api/search -H \"Content-Type: application/json\" -d '{\"query_text\": \"your question here\"}'${NC}"
