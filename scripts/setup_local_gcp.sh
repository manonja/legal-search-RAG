#!/bin/bash
# Script for setting up local development environment with GCP integration
set -e

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Legal Search RAG - Local GCP Setup${NC}"
echo "======================================="

# Check if .env file exists, create if not
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo -e "${YELLOW}Creating .env file from .env.example${NC}"
        cp .env.example .env
    else
        echo -e "${RED}No .env or .env.example file found. Creating empty .env file.${NC}"
        touch .env
    fi
fi

# Check if GCP credentials file path is provided
if [ $# -eq 0 ]; then
    echo -e "${YELLOW}Usage: $0 <path-to-gcp-credentials.json>${NC}"
    exit 1
fi

GCP_CREDS_PATH="$1"

# Check if file exists
if [ ! -f "$GCP_CREDS_PATH" ]; then
    echo -e "${RED}Error: GCP credentials file not found at $GCP_CREDS_PATH${NC}"
    exit 1
fi

# Get absolute path of credentials file
GCP_CREDS_PATH=$(realpath "$GCP_CREDS_PATH")

# Extract project ID from credentials file
PROJECT_ID=$(grep -o '"project_id": "[^"]*' "$GCP_CREDS_PATH" | cut -d'"' -f4)
if [ -z "$PROJECT_ID" ]; then
    echo -e "${YELLOW}Could not automatically extract project ID from credentials.${NC}"
    read -p "Please enter your GCP project ID: " PROJECT_ID
fi

# Prompt for bucket name
read -p "Enter your GCS bucket name (default: legal-search-docs): " BUCKET_NAME
BUCKET_NAME=${BUCKET_NAME:-"legal-search-docs"}

# Update .env file
echo -e "${BLUE}Updating .env file with GCP configuration...${NC}"

# Check if USE_GCP_STORAGE is already in .env
if grep -q "^USE_GCP_STORAGE=" .env; then
    # Update existing value
    sed -i '' "s/^USE_GCP_STORAGE=.*/USE_GCP_STORAGE=true/" .env
else
    # Add new value
    echo "USE_GCP_STORAGE=true" >> .env
fi

# Update or add GCP_PROJECT_ID
if grep -q "^GCP_PROJECT_ID=" .env; then
    sed -i '' "s|^GCP_PROJECT_ID=.*|GCP_PROJECT_ID=$PROJECT_ID|" .env
else
    echo "GCP_PROJECT_ID=$PROJECT_ID" >> .env
fi

# Update or add GCS_BUCKET_NAME
if grep -q "^GCS_BUCKET_NAME=" .env; then
    sed -i '' "s|^GCS_BUCKET_NAME=.*|GCS_BUCKET_NAME=$BUCKET_NAME|" .env
else
    echo "GCS_BUCKET_NAME=$BUCKET_NAME" >> .env
fi

# Update or add GOOGLE_APPLICATION_CREDENTIALS
if grep -q "^GOOGLE_APPLICATION_CREDENTIALS=" .env; then
    sed -i '' "s|^GOOGLE_APPLICATION_CREDENTIALS=.*|GOOGLE_APPLICATION_CREDENTIALS=$GCP_CREDS_PATH|" .env
else
    echo "GOOGLE_APPLICATION_CREDENTIALS=$GCP_CREDS_PATH" >> .env
fi

echo -e "${GREEN}GCP configuration added to .env file${NC}"

# Check if GCS_ENDPOINT is set (for testing with emulator)
read -p "Are you using a local GCS emulator for testing? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter GCS emulator endpoint (default: http://localhost:4443): " GCS_ENDPOINT
    GCS_ENDPOINT=${GCS_ENDPOINT:-"http://localhost:4443"}

    if grep -q "^GCS_ENDPOINT=" .env; then
        sed -i '' "s|^GCS_ENDPOINT=.*|GCS_ENDPOINT=$GCS_ENDPOINT|" .env
    else
        echo "GCS_ENDPOINT=$GCS_ENDPOINT" >> .env
    fi
    echo -e "${YELLOW}GCS emulator endpoint added to .env file${NC}"
fi

# Test GCP configuration
echo -e "${BLUE}Testing GCP configuration...${NC}"
python -c "
import os
from google.cloud import storage
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '$GCP_CREDS_PATH'
try:
    client = storage.Client(project='$PROJECT_ID')
    buckets = list(client.list_buckets(max_results=1))
    print('Successfully connected to GCP')
except Exception as e:
    print(f'Error: {str(e)}')
"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}GCP configuration test successful!${NC}"
    echo
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Upload test documents using:"
    echo "   python scripts/upload_to_gcs.py /path/to/document.pdf"
    echo "2. Process documents:"
    echo "   python -m process_docs"
    echo "3. Start the development server:"
    echo "   docker-compose up -d"
    echo
    echo -e "${GREEN}Setup completed successfully!${NC}"
else
    echo -e "${RED}GCP configuration test failed. Please check your credentials and try again.${NC}"
    exit 1
fi
