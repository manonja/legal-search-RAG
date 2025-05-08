#!/bin/bash

# docs_processor.sh - Script to process legal documents

# Find the project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

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
    echo "Usage: $0 [options]"
    echo "  -f, --files FILES      Files to process (can use wildcards in quotes)"
    echo "  -c, --chunk            Enable chunking after loading (default: false)"
    echo "  -o, --output DIR       Output directory for results (default: ./results)"
    echo "  -h, --help             Display this help message"
    exit 1
}

# Default values
files=""
enable_chunking=false
output_dir="$PROJECT_ROOT/results"

# Parse command-line arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -f|--files) files="$2"; shift ;;
        -c|--chunk) enable_chunking=true ;;
        -o|--output) output_dir="$2"; shift ;;
        -h|--help) usage ;;
        *) log_error "Unknown parameter: $1"; usage ;;
    esac
    shift
done

# Verify required parameters
if [ -z "$files" ]; then
    log_error "Error: Files parameter is required."
    usage
fi

# Create output directory if it doesn't exist
mkdir -p "$output_dir"

# Process file patterns
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

    matched_files=${#file_list[@]}
else
    # Use direct shell expansion for simple patterns
    matched_files=0
    for file in $files; do
        if [ -f "$file" ]; then
            ((matched_files++))
            file_list+=("$file")
        fi
    done
fi

if [ "$matched_files" -eq 0 ]; then
    log_error "Error: No files matched the pattern '$files'"
    exit 1
fi

log_info "Found $matched_files files to process"

# Create a temporary Python script for processing
TMP_SCRIPT=$(mktemp)
cat > "$TMP_SCRIPT" << 'EOF'
#!/usr/bin/env python3
import json
import sys
import os
from pathlib import Path
import traceback

def main():
    # Get arguments
    file_path = sys.argv[1]
    output_path = sys.argv[2]
    enable_chunking = sys.argv[3].lower() == "true"

    try:
        # Import required modules - fail gracefully if missing
        try:
            import fitz  # PyMuPDF for PDF processing
        except ImportError:
            print("Error: PyMuPDF (fitz) module not found. Please install: pip install pymupdf", file=sys.stderr)
            sys.exit(1)

        try:
            import docx  # python-docx for DOCX processing
        except ImportError:
            print("Error: python-docx module not found. Please install: pip install python-docx", file=sys.stderr)
            sys.exit(1)

        if enable_chunking:
            try:
                import semchunk
                import tiktoken
            except ImportError as e:
                module_name = str(e).split("'")[1] if "'" in str(e) else str(e)
                print(f"Error: {module_name} not found. Chunking disabled.", file=sys.stderr)
                enable_chunking = False

        # Process file based on extension
        path = Path(file_path)
        extension = path.suffix.lower()

        # Get file statistics
        file_stats = path.stat()
        file_info = {
            "filename": path.name,
            "path": str(path.absolute()),
            "size_bytes": file_stats.st_size,
            "processing_stages": []
        }

        # Step 1: Load document and extract text
        if extension == '.pdf':
            loader_type = "PDF"
            doc = fitz.open(file_path)

            # Extract text from each page
            extracted_text = ""
            for page in doc:
                extracted_text += page.get_text("text")

            # Extract metadata
            metadata = {"original_file_type": "pdf"}
            pdf_metadata = doc.metadata
            if pdf_metadata:
                for key, value in pdf_metadata.items():
                    if value:
                        metadata[f"pdf_{key.lower()}"] = value

            metadata["page_count"] = len(doc)

        elif extension == '.docx':
            loader_type = "DOCX"
            doc = docx.Document(file_path)

            # Extract text from paragraphs
            paragraphs = []
            for para in doc.paragraphs:
                if para.text:
                    paragraphs.append(para.text)

            # Join paragraphs with newlines
            extracted_text = "\n".join(paragraphs)

            # Get metadata
            metadata = {"original_file_type": "docx"}
            core_props = doc.core_properties
            if core_props:
                for prop in ['author', 'category', 'comments', 'content_status',
                            'created', 'identifier', 'keywords', 'language',
                            'last_modified_by', 'last_printed', 'modified',
                            'revision', 'subject', 'title', 'version']:
                    value = getattr(core_props, prop, None)
                    if value:
                        metadata[f"docx_{prop}"] = str(value)

        else:
            # Unsupported file type
            raise ValueError(f"Unsupported file extension: {extension}")

        # Record loading stage results
        loading_stage = {
            "stage": "Loading",
            "loader_used": loader_type,
            "text_extracted_chars": len(extracted_text),
            "metadata": metadata,
            "text_sample": extracted_text[:500] + ("..." if len(extracted_text) > 500 else "")
        }
        file_info["processing_stages"].append(loading_stage)

        # Step 2: Chunking (if enabled)
        if enable_chunking and extracted_text:
            import semchunk
            import tiktoken

            # Create document metadata
            doc_metadata = {
                "document_id": path.stem,
                "filename": path.name,
                "file_type": loader_type,
                "file_size": file_stats.st_size,
                **metadata
            }

            # Initialize chunker
            tokenizer_name = "cl100k_base"
            chunk_size = 512
            overlap = 50

            # Initialize tokenizer
            tokenizer = tiktoken.get_encoding(tokenizer_name)
            token_counter = lambda t: len(tokenizer.encode(t))

            # Initialize chunker
            chunker = semchunk.chunkerify(
                tokenizer_or_token_counter=token_counter,
                chunk_size=chunk_size
            )

            # Apply chunking
            text_chunks = chunker(extracted_text, overlap=overlap)

            chunks = []
            for i, chunk_text in enumerate(text_chunks, 1):
                # Count tokens in the chunk
                token_count = token_counter(chunk_text)

                # Create chunk object with metadata
                chunk = {
                    "text": chunk_text,
                    "metadata": {**doc_metadata, "chunk_index": i},
                    "token_count": token_count,
                }
                chunks.append(chunk)

            # Record chunking stage results
            chunking_stage = {
                "stage": "Chunking",
                "chunks_created": len(chunks),
                "chunker_used": "SemChunk",
                "sample_chunks": []
            }

            # Add sample chunks (limited to 3)
            for i, chunk in enumerate(chunks[:3]):
                chunk_sample = {
                    "chunk_index": chunk["metadata"]["chunk_index"],
                    "token_count": chunk["token_count"],
                    "text_sample": chunk["text"][:200] + ("..." if len(chunk["text"]) > 200 else "")
                }
                chunking_stage["sample_chunks"].append(chunk_sample)

            file_info["processing_stages"].append(chunking_stage)

        # Save results
        with open(output_path, "w") as f:
            json.dump(file_info, f, indent=2)

        # Success
        return 0

    except Exception as e:
        # Handle errors
        error_info = {
            "filename": Path(file_path).name,
            "error": f"Error processing {file_path}: {str(e)}",
            "traceback": traceback.format_exc()
        }

        try:
            with open(output_path, "w") as f:
                json.dump(error_info, f, indent=2)
        except:
            pass

        print(f"Error: {str(e)}", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
EOF

chmod +x "$TMP_SCRIPT"

# Initialize counters
processed=0
failed=0

# Process each file
for file in "${file_list[@]}"; do
    log_info "Processing $file... ($((processed+1))/$matched_files)"

    output_file="$output_dir/$(basename "$file").json"

    # Run the Python script to process the file
    if python3 "$TMP_SCRIPT" "$file" "$output_file" "$enable_chunking"; then
        log_success "Successfully processed $file, output: $output_file"
        ((processed++))
    else
        log_error "Failed to process $file"
        ((failed++))
    fi
done

# Clean up temp file
rm "$TMP_SCRIPT"

# Print summary
log_info "Processing completed."
log_success "Successfully processed: $processed/$matched_files files"
if [ "$failed" -gt 0 ]; then
    log_error "Failed processing: $failed/$matched_files files"
fi

log_info "Results saved to: $output_dir"

# Return appropriate exit code
if [ "$failed" -gt 0 ]; then
    exit 1
else
    exit 0
fi
