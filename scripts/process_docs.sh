#!/bin/bash

# Default directories
DEFAULT_INPUT_DIR="$HOME/Downloads/legaldocs"
DEFAULT_OUTPUT_DIR="$HOME/Downloads/processedLegalDocs"

# Help message
show_help() {
    echo "Usage: $0 [-i INPUT_DIR] [-o OUTPUT_DIR] [-h]"
    echo
    echo "Process legal documents using the RAG system"
    echo
    echo "Options:"
    echo "  -i INPUT_DIR   Directory containing input documents (default: $DEFAULT_INPUT_DIR)"
    echo "  -o OUTPUT_DIR  Directory for processed output (default: $DEFAULT_OUTPUT_DIR)"
    echo "  -h            Show this help message"
    exit 1
}

# Parse command line arguments
INPUT_DIR=$DEFAULT_INPUT_DIR
OUTPUT_DIR=$DEFAULT_OUTPUT_DIR

while getopts "i:o:h" opt; do
    case $opt in
        i) INPUT_DIR="$OPTARG";;
        o) OUTPUT_DIR="$OPTARG";;
        h) show_help;;
        \?) echo "Invalid option: -$OPTARG" >&2; show_help;;
    esac
done

# Create directories if they don't exist
mkdir -p "$INPUT_DIR"
mkdir -p "$OUTPUT_DIR"

# Export the directories as environment variables
export INPUT_DIR
export OUTPUT_DIR

# Run the processing script
echo "Processing documents..."
echo "Input directory: $INPUT_DIR"
echo "Output directory: $OUTPUT_DIR"
pixi run process-docs
