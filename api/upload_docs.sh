#!/bin/bash

# upload_docs.sh - Script to upload documents to the API

# Display usage information
usage() {
    echo "Usage: $0 -u URL -t TOKEN -f FILES"
    echo "  -u, --url URL      API endpoint URL"
    echo "  -t, --token TOKEN  Authorization token"
    echo "  -f, --files FILES  Files to upload (can use wildcards in quotes)"
    echo "  -h, --help         Display this help message"
    exit 1
}

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

# Verify required parameters
if [ -z "$url" ] || [ -z "$token" ] || [ -z "$files" ]; then
    echo "Error: URL, token, and files are required parameters."
    usage
fi

# Upload files
for file in $files; do
    if [ -f "$file" ]; then
        echo "Uploading $file..."
        curl -X POST "$url" \
            -H "Authorization: Bearer $token" \
            --form "file=@$file" \
            --silent | jq
        echo ""
        sleep 1
    else
        echo "Warning: $file not found or not a regular file. Skipping."
    fi
done

echo "Upload process completed."
