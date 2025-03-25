#!/bin/bash
# Script to help set up GCP credentials for Render.com deployments
set -e

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}GCP Credentials Setup for Render.com${NC}"
echo "======================================="

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

# Create Base64 encoded version of the credentials
echo -e "${BLUE}Creating Base64 encoded version of GCP credentials...${NC}"
GCP_CREDS_BASE64=$(base64 -i "$GCP_CREDS_PATH" | tr -d '\n')

# Output the encoded credentials
echo -e "${GREEN}GCP credentials encoded successfully!${NC}"
echo
echo -e "${YELLOW}Add the following environment variable to your Render.com service:${NC}"
echo
echo "GCP_CREDENTIALS_BASE64:"
echo "$GCP_CREDS_BASE64"
echo
echo -e "${YELLOW}Then add the following to your Render.com service's 'Start Command':${NC}"
echo
echo 'mkdir -p /app/credentials && echo "$GCP_CREDENTIALS_BASE64" | base64 -d > /app/credentials/gcp-key.json && exec "$@"'
echo
echo -e "${BLUE}This will decode the credentials at runtime and make them available to your application.${NC}"
echo -e "${GREEN}Don't forget to update your Dockerfile to set GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/gcp-key.json${NC}"

echo
echo -e "${YELLOW}Alternatively, you can add this to your Render.com service settings:${NC}"
echo -e "1. Open the advanced settings for your service"
echo -e "2. Add a Secret File:"
echo -e "   - Mount Path: /app/credentials/gcp-key.json"
echo -e "   - Contents: Paste the contents of your GCP credentials JSON file"
echo
echo -e "${GREEN}Done!${NC}"
