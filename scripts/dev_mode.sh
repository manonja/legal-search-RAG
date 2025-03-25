#!/bin/bash

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get script directory and project directory
SCRIPT_DIR=$(dirname "$(realpath "$0" 2>/dev/null || readlink -f "$0" 2>/dev/null || echo "$0")")
PROJECT_DIR=$(dirname "$SCRIPT_DIR")

# Change to project directory
cd "$PROJECT_DIR"

echo -e "${BLUE}Legal Search RAG - Development Mode${NC}"
echo "========================================"

# Check if tenant ID is provided as argument
if [ -n "$1" ]; then
    TENANT_ID="$1"
else
    # List existing tenants
    echo -e "${BLUE}Existing tenants:${NC}"
    ls -1 .env.* 2>/dev/null | sed 's/\.env\.//' | grep -v 'example' || echo -e "${YELLOW}No tenants found.${NC}"
    echo ""

    # Prompt for tenant ID
    read -p "Enter tenant ID to use: " TENANT_ID
fi

# Check if environment file exists
ENV_FILE=".env.$TENANT_ID"
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}Error: Environment file $ENV_FILE not found.${NC}"
    echo -e "${YELLOW}Please create a tenant first using the deploy_tenant.sh script.${NC}"
    exit 1
fi

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

echo -e "${GREEN}Starting development mode for tenant: $TENANT_ID${NC}"
echo -e "${YELLOW}Changes to API code will be automatically synced and the API container will restart.${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop watch mode (containers will continue running).${NC}"
echo ""

# Deploy tenant with watch mode
TENANT_ID="$TENANT_ID" ENV_FILE="$ENV_FILE" docker-compose --env-file "$ENV_FILE" watch
