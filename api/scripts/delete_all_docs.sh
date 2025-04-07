#!/bin/bash

# Find the .env file in the parent directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env"

# Source the .env file
if [ -f "$ENV_FILE" ]; then
  # Load API_TOKEN from .env
  export $(grep -v '^#' "$ENV_FILE" | xargs)
else
  echo "Error: .env file not found at $ENV_FILE"
  exit 1
fi

# Check if API_TOKEN is loaded
if [ -z "$API_TOKEN" ]; then
  echo "Error: API_TOKEN not found in .env file"
  exit 1
fi

# URL for your API
API_URL="https://maja-legal-api-dev-a43e97a-y52ot74ira-uc.a.run.app/api"
TOKEN="Bearer $API_TOKEN"

# Get all document IDs
echo "Fetching document IDs..."
DOCUMENT_IDS=$(curl -s -X GET \
  "${API_URL}/documents" \
  -H "Authorization: ${TOKEN}" \
  -H "Accept: application/json")

# Check if we got a valid response
if [[ $DOCUMENT_IDS == \[* ]]; then
  # Remove brackets and quotes, split into array
  DOCUMENT_IDS=$(echo $DOCUMENT_IDS | tr -d '[]"' | tr ',' ' ')

  echo "Found documents: $DOCUMENT_IDS"

  # Counter for successful deletions
  DELETED=0

  # Loop through each ID and delete
  for ID in $DOCUMENT_IDS; do
    echo "Deleting document: $ID"
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE \
      "${API_URL}/documents/$ID" \
      -H "Authorization: ${TOKEN}" \
      -H "Accept: application/json")

    if [ "$RESPONSE" == "204" ]; then
      echo "Successfully deleted $ID"
      ((DELETED++))
    else
      echo "Failed to delete $ID (status: $RESPONSE)"
    fi
  done

  echo "Completed! Deleted $DELETED out of $(echo $DOCUMENT_IDS | wc -w) documents."
else
  echo "Error fetching document IDs: $DOCUMENT_IDS"
fi
