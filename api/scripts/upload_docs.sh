#!/bin/bash

# upload_docs.sh - Script to upload documents to the API

# Find the .env file in the parent directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env"

# Display usage information
usage() {
    echo "Usage: $0 -u URL [-t TOKEN] -f FILES"
    echo "  -u, --url URL      API endpoint URL"
    echo "  -t, --token TOKEN  Authorization token (optional, defaults to API_TOKEN from .env)"
    echo "  -f, --files FILES  Files to upload (can use wildcards in quotes)"
    echo "  -h, --help         Display this help message"
    exit 1
}

# Source the .env file
if [ -f "$ENV_FILE" ]; then
    # Load API_TOKEN from .env
    export $(grep -v '^#' "$ENV_FILE" | xargs)
    echo "Found .env file at $ENV_FILE"
else
    echo "Warning: .env file not found at $ENV_FILE"
fi

# Parse command-line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -u|--url) url="$2"; shift ;;
        -t|--token) token="$2"; shift ;;
        -f|--files) files="$2"; shift ;;
        -h|--help) usage ;;
        *) echo "Unknown parameter: $1"; usage ;;
    esac
    shift
done

# If no token provided via CLI, use the one from .env
if [ -z "$token" ]; then
    # Check if API_TOKEN was loaded from .env
    if [ -n "$API_TOKEN" ]; then
        token="$API_TOKEN"
        echo "Using API token from .env file"
    else
        echo "Error: No token provided and API_TOKEN not found in .env file."
        usage
    fi
fi

# Verify required parameters
if [ -z "$url" ] || [ -z "$files" ]; then
    echo "Error: URL and files are required parameters."
    usage
fi

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    echo "Warning: jq is not installed. Output will not be formatted."
    JQ_FLAG=""
else
    JQ_FLAG="| jq"
fi

# Upload files
echo "Starting upload to $url"
echo "Using token: Bearer ${token:0:5}..."

# Count matched files
matched_files=0
for file in $files; do
    if [ -f "$file" ]; then
        ((matched_files++))
    fi
done

if [ "$matched_files" -eq 0 ]; then
    echo "Error: No files matched the pattern '$files'"
    exit 1
fi

echo "Found $matched_files files to upload"

# Upload each file
uploaded=0
for file in $files; do
    if [ -f "$file" ]; then
        echo "Uploading $file..."

        # Handle JQ formatting conditionally
        if [ -n "$JQ_FLAG" ]; then
            response=$(curl -X POST "$url" \
                -H "Authorization: Bearer $token" \
                --form "file=@$file" \
                --silent | jq .)
        else
            response=$(curl -X POST "$url" \
                -H "Authorization: Bearer $token" \
                --form "file=@$file" \
                --silent)
        fi

        echo "$response"
        echo ""
        ((uploaded++))
        echo "Progress: $uploaded/$matched_files"

        # Add delay between uploads
        if [ "$uploaded" -lt "$matched_files" ]; then
            sleep 1
        fi
    else
        echo "Warning: $file not found or not a regular file. Skipping."
    fi
done

echo "Upload process completed. Uploaded $uploaded/$matched_files files."
