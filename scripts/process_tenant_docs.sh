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

# Check if environment file exists
ENV_FILE=".env.$TENANT_ID"
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: Environment file $ENV_FILE not found.${NC}"
    exit 1
fi

# Load environment variables
source "$ENV_FILE"

# Set container paths
CONTAINER_INPUT_DIR="/app/tenants/$TENANT_ID/docs/input"
CONTAINER_OUTPUT_DIR="/app/tenants/$TENANT_ID/docs/output"
CONTAINER_CHUNKS_DIR="/app/tenants/$TENANT_ID/docs/chunks"

# Check documents in the container
DOC_COUNT=$(docker exec legal-search-api-$TENANT_ID ls -1 "$CONTAINER_INPUT_DIR" | grep -E '\.pdf$|\.docx$' | wc -l)

if [ "$DOC_COUNT" -eq 0 ]; then
    echo -e "${YELLOW}No documents found in $CONTAINER_INPUT_DIR${NC}"
    echo -e "${YELLOW}Please add PDF or DOCX documents to this directory first.${NC}"
    exit 1
fi

echo -e "${BLUE}Found $DOC_COUNT documents in input directory${NC}"

# Step 1: Process documents (convert to text)
echo -e "\n${BLUE}Step 1/3: Processing documents (extracting text)...${NC}"
docker exec -e TENANT_ID=$TENANT_ID \
    -e GOOGLE_API_KEY=$GOOGLE_API_KEY \
    -e INPUT_DIR=$CONTAINER_INPUT_DIR \
    -e OUTPUT_DIR=$CONTAINER_OUTPUT_DIR \
    legal-search-api-$TENANT_ID python3 -c "
import sys
sys.path.append('/app')
from process_docs import main
main()
"

# Check if processing was successful
if [ $? -ne 0 ]; then
    echo -e "${RED}Document processing failed. Check the logs above for errors.${NC}"
    exit 1
fi

# Step 2: Chunk documents
echo -e "\n${BLUE}Step 2/3: Chunking documents...${NC}"
docker exec -e TENANT_ID=$TENANT_ID \
    -e INPUT_DIR=$CONTAINER_OUTPUT_DIR \
    -e OUTPUT_DIR=$CONTAINER_CHUNKS_DIR \
    legal-search-api-$TENANT_ID python3 -c "
import sys
sys.path.append('/app')
from chunk import main
main()
"

# Check if chunking was successful
if [ $? -ne 0 ]; then
    echo -e "${RED}Document chunking failed. Check the logs above for errors.${NC}"
    exit 1
fi

# Step 3: Generate embeddings
echo -e "\n${BLUE}Step 3/3: Generating embeddings (this may take a while)...${NC}"
docker exec -e TENANT_ID=$TENANT_ID \
    -e OPENAI_API_KEY=$OPENAI_API_KEY \
    -e CHUNKS_DIR=$CONTAINER_CHUNKS_DIR \
    legal-search-api-$TENANT_ID python3 -c "
import sys
sys.path.append('/app')
from embeddings import main
main()
"

# Check if embedding generation was successful
if [ $? -ne 0 ]; then
    echo -e "${RED}Embedding generation failed. Check the logs above for errors.${NC}"
    exit 1
fi

# Get file counts
OUTPUT_FILES=$(docker exec legal-search-api-$TENANT_ID ls -1 "$CONTAINER_OUTPUT_DIR" 2>/dev/null | grep -v "^test1$" | wc -l)
CHUNKS_FILES=$(docker exec legal-search-api-$TENANT_ID ls -1 "$CONTAINER_CHUNKS_DIR" 2>/dev/null | wc -l)

# Check output directories
echo -e "\n${GREEN}Processing complete!${NC}"
echo -e "${BLUE}Processed document stats:${NC}"
echo -e "  Input files: $DOC_COUNT files"
echo -e "  Processed text files: $OUTPUT_FILES files"
echo -e "  Chunked files: $CHUNKS_FILES files"
echo -e "  Vector DB: ChromaDB at /app/cache/chroma/$TENANT_ID/"

# Remind about API endpoints
API_PORT=$(grep "^API_PORT=" .env.$TENANT_ID 2>/dev/null | cut -d= -f2)
FRONTEND_PORT=$(grep "^FRONTEND_PORT=" .env.$TENANT_ID 2>/dev/null | cut -d= -f2)

echo -e "\n${BLUE}Your RAG system is ready for queries!${NC}"
echo -e "  API: ${GREEN}http://localhost:$API_PORT${NC}"
echo -e "  Frontend: ${GREEN}http://localhost:$FRONTEND_PORT${NC}"
echo -e "\n${BLUE}Example API query:${NC}"
echo -e "${GREEN}curl -X POST http://localhost:$API_PORT/api/search -H \"Content-Type: application/json\" -d '{\"query_text\": \"your question here\"}'${NC}"
