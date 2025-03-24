#!/bin/bash

# Colors for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}   Legal Search RAG - Add Documents to Tenant     ${NC}"
echo -e "${BLUE}==================================================${NC}"
echo ""

# Get script directory
SCRIPT_DIR=$(dirname "$(realpath "$0" 2>/dev/null || readlink -f "$0" 2>/dev/null || echo "$0")")
PROJECT_DIR=$(dirname "$SCRIPT_DIR")

# Change to project directory
cd "$PROJECT_DIR"

# Check if tenant ID is provided as argument
if [ -z "$1" ]; then
    # List existing tenants
    echo -e "${BLUE}Existing tenants:${NC}"

    TENANTS=$(docker ps -a --format '{{.Names}}' | grep "legal-search-api-" | sed 's/legal-search-api-//')

    if [ -z "$TENANTS" ]; then
        echo -e "${YELLOW}No tenants found. Please create a tenant first with deploy_tenant.sh${NC}"
        exit 1
    fi

    echo -e "${GREEN}Tenant ID           Status${NC}"
    echo -e "---------------------------------"

    for tenant in $TENANTS; do
        local status=$(docker ps --format '{{.Status}}' -f "name=legal-search-api-$tenant" | cut -d' ' -f1)
        if [ -z "$status" ]; then
            status="Stopped"
        fi

        printf "%-20s %-15s\n" "$tenant" "$status"
    done

    echo ""
    read -p "Enter tenant ID to add documents to: " tenant_id
else
    tenant_id=$1
fi

# Validate tenant exists
if ! docker ps -a --format '{{.Names}}' | grep -q "legal-search-api-$tenant_id"; then
    echo -e "${RED}Error: Tenant '$tenant_id' not found.${NC}"
    exit 1
fi

# Check if tenant is running
if ! docker ps --format '{{.Names}}' | grep -q "legal-search-api-$tenant_id"; then
    echo -e "${YELLOW}Warning: Tenant '$tenant_id' is not running.${NC}"
    read -p "Do you want to start it now? (y/n): " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}Starting tenant...${NC}"
        ENV_FILE=".env.$tenant_id" docker-compose --env-file ".env.$tenant_id" up -d
    else
        echo -e "${YELLOW}Please start the tenant before processing documents.${NC}"
        exit 1
    fi
fi

# Define input directory
INPUT_DIR="$PROJECT_DIR/tenants/$tenant_id/docs/input"
mkdir -p "$INPUT_DIR"

# Ask for document source
echo ""
echo -e "${BLUE}Document source options:${NC}"
echo -e "1. ${GREEN}Select files using file picker${NC}"
echo -e "2. ${GREEN}Specify a directory to copy from${NC}"
echo -e "3. ${GREEN}Manual copy (I'll copy files myself)${NC}"
echo ""
read -p "Choose an option (1-3): " src_option

case $src_option in
    1)
        # This is OS-dependent, for macOS
        if [[ "$OSTYPE" == "darwin"* ]]; then
            echo -e "${YELLOW}Select files in the Finder dialog${NC}"
            SRC_FILES=$(osascript -e 'set fileList to choose file with multiple selections allowed with prompt "Select legal documents to import"' -e 'set output to ""' -e 'repeat with aFile in fileList' -e 'set output to output & POSIX path of aFile & "\n"' -e 'end repeat' -e 'return output')

            if [ -z "$SRC_FILES" ]; then
                echo -e "${RED}No files selected.${NC}"
                exit 1
            fi

            echo -e "${BLUE}Copying selected files to $INPUT_DIR${NC}"
            echo "$SRC_FILES" | while read file; do
                if [ -n "$file" ]; then
                    cp "$file" "$INPUT_DIR/"
                    echo -e "${GREEN}Copied: $(basename "$file")${NC}"
                fi
            done
        else
            echo -e "${YELLOW}File picker is only available on macOS.${NC}"
            echo -e "${YELLOW}Please choose option 2 or 3 instead.${NC}"
            exit 1
        fi
        ;;
    2)
        read -p "Enter the path to the directory containing your documents: " src_dir

        if [ ! -d "$src_dir" ]; then
            echo -e "${RED}Error: Directory not found.${NC}"
            exit 1
        fi

        # Copy PDF and DOCX files
        echo -e "${BLUE}Copying documents from $src_dir to $INPUT_DIR${NC}"
        find "$src_dir" -type f \( -name "*.pdf" -o -name "*.PDF" -o -name "*.docx" -o -name "*.DOCX" -o -name "*.doc" -o -name "*.DOC" \) -exec cp {} "$INPUT_DIR/" \;

        # Count copied files
        copied_count=$(find "$INPUT_DIR" -type f \( -name "*.pdf" -o -name "*.PDF" -o -name "*.docx" -o -name "*.DOCX" -o -name "*.doc" -o -name "*.DOC" \) | wc -l | tr -d ' ')

        echo -e "${GREEN}Copied $copied_count documents.${NC}"
        ;;
    3)
        echo -e "${YELLOW}Please copy your documents to: $INPUT_DIR${NC}"
        echo -e "${YELLOW}Supported formats: PDF, DOC, DOCX${NC}"

        read -p "Press Enter when you've finished copying your documents..."

        # Count files
        doc_count=$(find "$INPUT_DIR" -type f \( -name "*.pdf" -o -name "*.PDF" -o -name "*.docx" -o -name "*.DOCX" -o -name "*.doc" -o -name "*.DOC" \) | wc -l | tr -d ' ')

        if [ "$doc_count" -eq 0 ]; then
            echo -e "${RED}No documents found in $INPUT_DIR${NC}"
            exit 1
        fi

        echo -e "${GREEN}Found $doc_count documents.${NC}"
        ;;
    *)
        echo -e "${RED}Invalid option.${NC}"
        exit 1
        ;;
esac

# Process the documents
echo ""
echo -e "${BLUE}Ready to process documents for tenant: $tenant_id${NC}"
read -p "Process documents now? (y/n): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Processing documents...${NC}"
    bash "$SCRIPT_DIR/process_tenant_docs.sh" "$tenant_id"
else
    echo -e "${YELLOW}You can process your documents later using:${NC}"
    echo -e "${GREEN}./scripts/process_tenant_docs.sh $tenant_id${NC}"
fi

# Done
echo ""
echo -e "${GREEN}Document addition complete!${NC}"
echo -e "${YELLOW}Your documents are in: $INPUT_DIR${NC}"
echo ""
