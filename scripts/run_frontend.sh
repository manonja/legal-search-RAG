#!/bin/bash

# Colors for output formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}Legal Search RAG - Frontend Development${NC}"
echo "========================================"

# Function to check if a port is available
check_port() {
    local port=$1
    if command -v lsof >/dev/null 2>&1; then
        if lsof -i :"$port" >/dev/null 2>&1; then
            return 1 # Port is in use
        else
            return 0 # Port is available
        fi
    else
        # If lsof is not available, try nc
        if command -v nc >/dev/null 2>&1; then
            nc -z localhost "$port" >/dev/null 2>&1
            if [ $? -eq 0 ]; then
                return 1 # Port is in use
            else
                return 0 # Port is available
            fi
        fi
    fi

    # If we can't check, assume it's available
    return 0
}

# Check if frontend directory exists
FRONTEND_DIR="$PROJECT_DIR/frontend"
if [ ! -d "$FRONTEND_DIR" ]; then
    echo -e "${RED}Error: Frontend directory not found at $FRONTEND_DIR${NC}"
    exit 1
fi

# Extract API port from .env
API_PORT=8000
if [ -f "$PROJECT_DIR/api/.env" ]; then
    ENV_API_PORT=$(grep "API_PORT" "$PROJECT_DIR/api/.env" | cut -d '=' -f2 | sed 's/"//g' | sed "s/'//g")
    if [ -n "$ENV_API_PORT" ]; then
        API_PORT=$ENV_API_PORT
    fi
fi

# Check frontend port (default 3000)
FRONTEND_PORT=3000
if ! check_port "$FRONTEND_PORT"; then
    echo -e "${RED}Warning: Port $FRONTEND_PORT is already in use.${NC}"
    echo -e "${YELLOW}The frontend may not start properly.${NC}"
    echo "You can modify the port in frontend/package.json or stop the process using this port."
fi

# Create .env.local file for the frontend
echo -e "${BLUE}Creating environment file for frontend...${NC}"
cat > "$FRONTEND_DIR/.env.local" << EOF
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:$API_PORT
EOF

echo -e "${GREEN}Created frontend environment file at $FRONTEND_DIR/.env.local${NC}"
echo -e "${YELLOW}API URL set to: http://localhost:$API_PORT${NC}"

# Check if API is running
if check_port "$API_PORT"; then
    echo -e "${YELLOW}Warning: API server does not appear to be running on port $API_PORT${NC}"
    echo -e "${YELLOW}Please start the API server first in another terminal:${NC}"
    echo -e "  ${GREEN}./scripts/run_local.sh${NC}"
else
    echo -e "${GREEN}API server detected on port $API_PORT${NC}"
fi

echo -e "${BLUE}Starting frontend development server...${NC}"
echo -e "${YELLOW}Frontend will be available at http://localhost:$FRONTEND_PORT${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"

cd "$FRONTEND_DIR" && npm run dev
