#!/bin/bash

# upload_docs.sh - Script to upload documents to the API
# This script handles uploading documents to the Legal Search RAG API

# Find the .env file in the parent directory
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
    echo "Usage: $0 -u URL [-t TOKEN] -f FILES"
    echo "  -u, --url URL      API endpoint URL"
    echo "  -t, --token TOKEN  Authorization token (optional, defaults to API_TOKEN from .env)"
    echo "  -f, --files FILES  Files to upload (can use wildcards in quotes)"
    echo "  -h, --help         Display this help message"
    exit 1
}

# Source the .env file
if [ -f "$ENV_FILE" ]; then
    # Load API_TOKEN from .env - only export lines that are properly formatted key=value pairs
    log_info "Found .env file at $ENV_FILE"
    export $(grep -v '^#' "$ENV_FILE" | grep '=' | sed 's/ *#.*//g' | xargs)
else
    log_warning "Warning: .env file not found at $ENV_FILE"
fi

# Parse command-line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -u|--url) url="$2"; shift ;;
        -t|--token) token="$2"; shift ;;
        -f|--files) files="$2"; shift ;;
        -h|--help) usage ;;
        *) log_error "Unknown parameter: $1"; usage ;;
    esac
    shift
done

# If no token provided via CLI, use the one from .env
if [ -z "$token" ]; then
    # Check if API_TOKEN was loaded from .env
    if [ -n "$API_TOKEN" ]; then
        token="$API_TOKEN"
        log_info "Using API token from .env file"
    else
        log_error "Error: No token provided and API_TOKEN not found in .env file."
        usage
    fi
fi

# Verify required parameters
if [ -z "$url" ] || [ -z "$files" ]; then
    log_error "Error: URL and files are required parameters."
    usage
fi

# Check if jq is installed
if ! command -v jq &> /dev/null; then
    log_warning "Warning: jq is not installed. Output will not be formatted."
    JQ_FLAG=""
else
    JQ_FLAG="| jq"
fi

# Upload files
log_info "Starting upload to $url"
log_info "Using token: Bearer ${token:0:5}..."

# Detect if we need to use find for file matching (for complex patterns)
if [[ "$files" == *"{"*"}"* ]]; then
    # Extract the base directory and patterns from the file pattern
    base_dir=$(dirname "$files")
    pattern=$(basename "$files")

    # Extract file extensions from the pattern
    extensions=$(echo "$pattern" | grep -o "{.*}" | tr -d "{}" | tr "," " ")

    # Use find to get files with the specified extensions
    file_list=()
    for ext in $extensions; do
        while IFS= read -r file; do
            file_list+=("$file")
        done < <(find "$base_dir" -type f -name "*.$ext" 2>/dev/null)
    done

    # Count matched files
    matched_files=${#file_list[@]}
else
    # Use direct shell expansion for simple patterns
    matched_files=0
    for file in $files; do
        if [ -f "$file" ]; then
            ((matched_files++))
        fi
    done
fi

if [ "$matched_files" -eq 0 ]; then
    log_error "Error: No files matched the pattern '$files'"
    exit 1
fi

log_info "Found $matched_files files to upload"

# Initialize counters
uploaded=0
failed=0

# Upload each file - either from file list array or direct shell expansion
if [[ ${#file_list[@]} -gt 0 ]]; then
    # Use the files from the file_list array
    for file in "${file_list[@]}"; do
        log_info "Uploading $file... ($((uploaded+1))/$matched_files)"

        # Handle JQ formatting conditionally
        if [ -n "$JQ_FLAG" ]; then
            response=$(curl -X POST "$url" \
                -H "Authorization: Bearer $token" \
                --form "file=@$file" \
                --silent | jq .)
            http_code=$?
        else
            response=$(curl -X POST "$url" \
                -H "Authorization: Bearer $token" \
                --form "file=@$file" \
                --silent)
            http_code=$?
        fi

        # Check HTTP response and curl exit code
        if [ $http_code -ne 0 ]; then
            log_error "Failed to upload $file (HTTP error $http_code)"
            ((failed++))
        elif [[ "$response" == *"error"* ]] || [[ "$response" == *"Error"* ]]; then
            log_error "Failed to upload $file: $response"
            ((failed++))
        else
            log_success "Successfully uploaded $file"
            echo "$response"
            ((uploaded++))
        fi

        # Add delay between uploads to avoid overwhelming the server
        if [ "$uploaded" -lt "$matched_files" ]; then
            sleep 1
        fi
    done
else
    # Use direct shell expansion
    for file in $files; do
        if [ -f "$file" ]; then
            log_info "Uploading $file... ($((uploaded+1))/$matched_files)"

            # Handle JQ formatting conditionally
            if [ -n "$JQ_FLAG" ]; then
                response=$(curl -X POST "$url" \
                    -H "Authorization: Bearer $token" \
                    --form "file=@$file" \
                    --silent | jq .)
                http_code=$?
            else
                response=$(curl -X POST "$url" \
                    -H "Authorization: Bearer $token" \
                    --form "file=@$file" \
                    --silent)
                http_code=$?
            fi

            # Check HTTP response and curl exit code
            if [ $http_code -ne 0 ]; then
                log_error "Failed to upload $file (HTTP error $http_code)"
                ((failed++))
            elif [[ "$response" == *"error"* ]] || [[ "$response" == *"Error"* ]]; then
                log_error "Failed to upload $file: $response"
                ((failed++))
            else
                log_success "Successfully uploaded $file"
                echo "$response"
                ((uploaded++))
            fi

            # Add delay between uploads
            if [ "$uploaded" -lt "$matched_files" ]; then
                sleep 1
            fi
        else
            log_warning "Warning: $file not found or not a regular file. Skipping."
        fi
    done
fi

# Print summary
log_info "Upload process completed."
log_success "Successfully uploaded: $uploaded/$matched_files files"
if [ "$failed" -gt 0 ]; then
    log_error "Failed uploads: $failed/$matched_files files"
fi

# Return appropriate exit code
if [ "$failed" -gt 0 ]; then
    exit 1
else
    exit 0
fi
