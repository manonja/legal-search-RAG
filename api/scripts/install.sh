#!/bin/bash

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Legal Search RAG API - Dependency Installation${NC}"
echo "======================================================"

# Try to install with uv first
echo -e "${YELLOW}Attempting to install dependencies with uv...${NC}"

if command -v uv &> /dev/null; then
    # uv is available
    echo "uv is installed, using it for dependency installation"

    # Try to install with uv
    uv pip install -e . -v
    UV_EXIT_CODE=$?

    if [ $UV_EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}✅ Dependencies installed successfully with uv${NC}"
    else
        echo -e "${RED}❌ Failed to install dependencies with uv (exit code: $UV_EXIT_CODE)${NC}"
        echo -e "${YELLOW}Falling back to pip...${NC}"

        # Try to install with pip instead
        pip install -r requirements.txt
        PIP_EXIT_CODE=$?

        if [ $PIP_EXIT_CODE -eq 0 ]; then
            echo -e "${GREEN}✅ Dependencies installed successfully with pip${NC}"
        else
            echo -e "${RED}❌ Failed to install dependencies with pip (exit code: $PIP_EXIT_CODE)${NC}"
            echo "Please check your Python environment and try again"
            exit 1
        fi
    fi
else
    # uv is not available, use pip
    echo -e "${YELLOW}uv is not installed, using pip instead${NC}"
    pip install -r requirements.txt
    PIP_EXIT_CODE=$?

    if [ $PIP_EXIT_CODE -eq 0 ]; then
        echo -e "${GREEN}✅ Dependencies installed successfully with pip${NC}"
    else
        echo -e "${RED}❌ Failed to install dependencies with pip (exit code: $PIP_EXIT_CODE)${NC}"
        echo "Please check your Python environment and try again"
        exit 1
    fi
fi

# Verify dependencies
echo -e "\n${YELLOW}Verifying installed dependencies...${NC}"
python scripts/check-dependencies.py

CHECK_DEPS_EXIT_CODE=$?
if [ $CHECK_DEPS_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ All dependencies verified${NC}"
    echo -e "${GREEN}Installation complete! You can now run the application with:${NC}"
    echo -e "${YELLOW}make serve-api${NC}"
else
    echo -e "${RED}❌ Some dependencies could not be verified${NC}"
    echo -e "${YELLOW}You may need to troubleshoot your environment before running the application${NC}"
    exit 1
fi
