#!/bin/bash

# Colors for terminal output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Testing Search Endpoint with RunPod${NC}"

# Set API URL and test query
API_URL="http://localhost:8000/api"
TEST_QUERY="What are the key legal provisions?"

# Check if API_TOKEN is set, default to test-token if not
API_TOKEN=${API_TOKEN:-test-token}
AUTH_HEADER="Authorization: Bearer ${API_TOKEN}"

# Test the search endpoint
echo -e "\n${YELLOW}Testing search endpoint with query: '${TEST_QUERY}'${NC}"
curl -X POST "${API_URL}/search" \
  -H "${AUTH_HEADER}" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"${TEST_QUERY}\", \"limit\": 5}" | jq

# Check if the search was successful
if [ $? -ne 0 ]; then
  echo -e "${RED}Search request failed${NC}"
  exit 1
fi

echo -e "\n${GREEN}Search test completed${NC}"

# Provide additional debugging commands
echo -e "\n${YELLOW}Additional commands for debugging:${NC}"
echo -e "${GREEN}Check server logs:${NC} cat api_server.log"
echo -e "${GREEN}Test with longer timeout:${NC} curl -X POST '${API_URL}/search' -H '${AUTH_HEADER}' -H 'Content-Type: application/json' -d '{\"query\": \"${TEST_QUERY}\", \"limit\": 5}' --max-time 60 | jq"
echo -e "${GREEN}Test RAG search:${NC} curl -X POST '${API_URL}/rag-search' -H '${AUTH_HEADER}' -H 'Content-Type: application/json' -d '{\"query\": \"${TEST_QUERY}\", \"max_results\": 5, \"temperature\": 0.7, \"max_tokens\": 1000}' | jq"
