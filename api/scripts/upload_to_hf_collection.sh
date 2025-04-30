#!/bin/bash

# upload_to_hf_collection.sh - Script to create a HuggingFace collection and upload documents
# This script creates a new ChromaDB collection with HuggingFace embeddings and uploads documents to it

# Find script directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env"

# Set up logging
log() {
  local level="$1"
  local message="$2"
  local timestamp=$(date "+%Y-%m-%d %H:%M:%S")
  echo "[$timestamp] [$level] $message"
}

log_info() { log "INFO" "$1"; }
log_error() { log "ERROR" "$1" >&2; }
log_warning() { log "WARNING" "$1" >&2; }
log_success() { log "SUCCESS" "$1"; }

# Display usage information
usage() {
    echo "Usage: $0 -n COLLECTION_NAME -u URL -f FILES [-t TOKEN] [--force]"
    echo "  -n, --name NAME    Collection name (optional, default is {COLLECTION_NAME}_hf)"
    echo "  -u, --url URL      API endpoint URL"
    echo "  -f, --files FILES  Files to upload (can use wildcards in quotes)"
    echo "  -t, --token TOKEN  Authorization token (optional, defaults to API_TOKEN from .env)"
    echo "  --force            Force recreation of the collection if it already exists"
    echo "  -h, --help         Display this help message"
    exit 1
}

# Source the .env file
if [ -f "$ENV_FILE" ]; then
    log_info "Found .env file at $ENV_FILE"
    export $(grep -v '^#' "$ENV_FILE" | grep '=' | sed 's/ *#.*//g' | xargs)
else
    log_warning "Warning: .env file not found at $ENV_FILE"
fi

# Parse command-line arguments
FORCE_FLAG=""
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -n|--name) collection_name="$2"; shift ;;
        -u|--url) url="$2"; shift ;;
        -t|--token) token="$2"; shift ;;
        -f|--files) files="$2"; shift ;;
        --force) FORCE_FLAG="--force" ;;
        -h|--help) usage ;;
        *) log_error "Unknown parameter: $1"; usage ;;
    esac
    shift
done

# Check for required parameters
if [ -z "$url" ] || [ -z "$files" ]; then
    log_error "Error: URL and files are required parameters."
    usage
fi

# Step 1: Create the HuggingFace collection
log_info "Step 1: Creating HuggingFace collection"

# Build arguments for the Python script
PYTHON_ARGS=""
if [ -n "$collection_name" ]; then
    PYTHON_ARGS="--name $collection_name"
fi
if [ -n "$FORCE_FLAG" ]; then
    PYTHON_ARGS="$PYTHON_ARGS --force"
fi

# Run the Python script to create the collection
cd "$PROJECT_ROOT"
python "$SCRIPT_DIR/create_hf_collection.py" $PYTHON_ARGS

if [ $? -ne 0 ]; then
    log_error "Failed to create HuggingFace collection. Aborting."
    exit 1
fi

log_success "HuggingFace collection created successfully"

# Step 2: Upload documents
log_info "Step 2: Uploading documents to collection"

# Add collection name to URL if specified
upload_url="${url}"
if [ -n "$collection_name" ]; then
    # Check if URL already has query parameters
    if [[ "$upload_url" == *"?"* ]]; then
        upload_url="${upload_url}&collection_name=${collection_name}"
    else
        upload_url="${upload_url}?collection_name=${collection_name}"
    fi
    log_info "Using upload URL with collection parameter: $upload_url"
fi

# Build arguments for the upload script
UPLOAD_ARGS="-u \"$upload_url\" -f '$files'"
if [ -n "$token" ]; then
    UPLOAD_ARGS="$UPLOAD_ARGS -t $token"
fi

# Run the upload script
eval "$SCRIPT_DIR/upload_docs.sh $UPLOAD_ARGS"

if [ $? -ne 0 ]; then
    log_error "Document upload process completed with errors."
    exit 1
fi

log_success "All documents uploaded successfully to the HuggingFace collection"
exit 0
