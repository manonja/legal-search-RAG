#!/bin/bash

# Colors for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}   Legal Search RAG - Quick Start Guide           ${NC}"
echo -e "${BLUE}==================================================${NC}"
echo ""
echo -e "${GREEN}This script will help you set up your first tenant and process documents${NC}"
echo ""

# Get script directory
SCRIPT_DIR=$(dirname "$(realpath "$0" 2>/dev/null || readlink -f "$0" 2>/dev/null || echo "$0")")
PROJECT_DIR=$(dirname "$SCRIPT_DIR")

# Change to project directory
cd "$PROJECT_DIR"

# Step 1: Check prerequisites
echo -e "${BLUE}Step 1: Checking prerequisites...${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed. Please install Docker first.${NC}"
    echo -e "${YELLOW}Visit https://docs.docker.com/get-docker/ for installation instructions.${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed. Please install Docker Compose first.${NC}"
    echo -e "${YELLOW}Visit https://docs.docker.com/compose/install/ for installation instructions.${NC}"
    exit 1
fi

echo -e "${GREEN}All prerequisites are met.${NC}"
echo ""

# Step 2: Create new tenant
echo -e "${BLUE}Step 2: Creating a new tenant...${NC}"
echo ""

# Ask for tenant ID
read -p "Enter a name for your tenant (alphanumeric, hyphens, underscores only): " tenant_id

# Validate tenant ID
if [[ ! $tenant_id =~ ^[a-zA-Z0-9_-]+$ ]]; then
    echo -e "${RED}Error: Tenant ID must consist of alphanumeric characters, hyphens, or underscores only.${NC}"
    exit 1
fi

# Launch deploy_tenant.sh with option 1
echo -e "${YELLOW}Launching tenant deployment script...${NC}"
echo -e "${YELLOW}When prompted:${NC}"
echo -e "  1. Enter '$tenant_id' as the tenant ID"
echo -e "  2. Edit the environment file to add your API keys"
echo -e "  3. Select 'y' when asked to deploy now"
echo ""

# Start the deployment script and send the choice
bash "$SCRIPT_DIR/deploy_tenant.sh"

# Wait for deployment to complete
echo -e "${BLUE}Step 3: Preparing for document processing...${NC}"
echo ""

# Check if the tenant was created
if ! docker ps | grep -q "legal-search-api-$tenant_id"; then
    echo -e "${RED}Error: Tenant deployment failed or was cancelled.${NC}"
    exit 1
fi

# Step 4: Add documents
echo -e "${BLUE}Step 4: Adding documents...${NC}"
echo ""

INPUT_DIR="$PROJECT_DIR/tenants/$tenant_id/docs/input"
mkdir -p "$INPUT_DIR"

echo -e "${YELLOW}Document input directory: $INPUT_DIR${NC}"
echo -e "Please copy your PDF or DOCX legal documents to this directory."
echo ""

read -p "Have you copied your documents to the input directory? (y/n): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Please copy your documents to $INPUT_DIR and then run:${NC}"
    echo -e "${GREEN}./scripts/process_tenant_docs.sh $tenant_id${NC}"
    exit 0
fi

# Count documents
DOC_COUNT=$(ls -1 "$INPUT_DIR" 2>/dev/null | wc -l | tr -d ' ')

if [ "$DOC_COUNT" -eq 0 ]; then
    echo -e "${RED}No documents found in $INPUT_DIR${NC}"
    echo -e "${YELLOW}Please add PDF or DOCX documents to this directory and then run:${NC}"
    echo -e "${GREEN}./scripts/process_tenant_docs.sh $tenant_id${NC}"
    exit 1
fi

echo -e "${GREEN}Found $DOC_COUNT documents.${NC}"
echo ""

# Step 5: Process documents
echo -e "${BLUE}Step 5: Processing documents...${NC}"
echo ""

echo -e "${YELLOW}This step will:${NC}"
echo -e "  1. Extract text from your documents"
echo -e "  2. Split documents into chunks"
echo -e "  3. Generate embeddings using OpenAI API"
echo -e "${YELLOW}This may take several minutes depending on the number and size of your documents.${NC}"
echo ""

read -p "Start document processing now? (y/n): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}You can process your documents later using:${NC}"
    echo -e "${GREEN}./scripts/process_tenant_docs.sh $tenant_id${NC}"
    exit 0
fi

# Process documents
bash "$SCRIPT_DIR/process_tenant_docs.sh" "$tenant_id"

# Step 6: Access the system
echo -e "\n${BLUE}Step 6: Accessing your RAG system...${NC}"
echo ""

# Get tenant ports
API_PORT=$(grep "^API_PORT=" ".env.$tenant_id" 2>/dev/null | cut -d= -f2)
FRONTEND_PORT=$(grep "^FRONTEND_PORT=" ".env.$tenant_id" 2>/dev/null | cut -d= -f2)

echo -e "${GREEN}Setup complete! Your legal search RAG system is ready.${NC}"
echo -e "${BLUE}Access your system at:${NC}"
echo -e "  Frontend: ${GREEN}http://localhost:$FRONTEND_PORT${NC}"
echo -e "  API: ${GREEN}http://localhost:$API_PORT${NC}"
echo ""
echo -e "${YELLOW}For more information on using and managing your system, see:${NC}"
echo -e "${GREEN}MULTI_TENANT_DEPLOYMENT.md${NC}"
echo ""
