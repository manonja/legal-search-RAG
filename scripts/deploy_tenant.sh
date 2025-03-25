#!/bin/bash
set -e

# Color codes for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
DEFAULT_BASE_PORT=8000
DEFAULT_PORT_INCREMENT=100

# Detect OS for platform-specific commands
OS_TYPE=$(uname)
SED_INPLACE=""
if [[ "$OS_TYPE" == "Darwin" ]]; then
    # macOS requires an extension argument for -i, even if it's empty
    SED_INPLACE="-i ''"
else
    # Linux and other Unix systems don't need the empty extension
    SED_INPLACE="-i"
fi

# Display header
echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}   Legal Search RAG - Multi-Tenant Deployment     ${NC}"
echo -e "${BLUE}==================================================${NC}"

# Get script directory
SCRIPT_DIR=$(dirname "$(realpath "$0" 2>/dev/null || readlink -f "$0" 2>/dev/null || echo "$0")")
PROJECT_DIR=$(dirname "$SCRIPT_DIR")

# Change to project directory
cd "$PROJECT_DIR"

# Function to validate tenant ID
validate_tenant_id() {
    local tenant_id=$1
    if [[ ! $tenant_id =~ ^[a-zA-Z0-9_-]+$ ]]; then
        echo -e "${RED}Error: Tenant ID must consist of alphanumeric characters, hyphens, or underscores only.${NC}"
        return 1
    fi
    return 0
}

# Function to check if tenant already exists
tenant_exists() {
    local tenant_id=$1
    if docker ps -a --format '{{.Names}}' | grep -q "legal-search-api-$tenant_id$"; then
        return 0
    else
        return 1
    fi
}

# Function to find available ports
find_available_ports() {
    local base_port=$1
    local increment=$2
    local tenant_count=$(docker ps -a --format '{{.Names}}' | grep -c "legal-search-api-")

    # Calculate port offsets based on existing tenants
    local api_port=$((base_port + (tenant_count * increment)))
    local frontend_port=$((api_port + 1))
    local http_port=$((api_port + 2))
    local https_port=$((api_port + 3))

    # Ensure ports are available
    while netstat -tuln 2>/dev/null | grep -q ":$api_port " || \
          netstat -tuln 2>/dev/null | grep -q ":$frontend_port " || \
          netstat -tuln 2>/dev/null | grep -q ":$http_port " || \
          netstat -tuln 2>/dev/null | grep -q ":$https_port "; do
        api_port=$((api_port + increment))
        frontend_port=$((api_port + 1))
        http_port=$((api_port + 2))
        https_port=$((api_port + 3))
    done

    echo "$api_port $frontend_port $http_port $https_port"
}

# Function to create environment file for tenant
create_tenant_env() {
    local tenant_id=$1
    local api_port=$2
    local frontend_port=$3
    local http_port=$4
    local https_port=$5
    local env_file=".env.$tenant_id"

    echo -e "${BLUE}Creating environment file for tenant: ${GREEN}$tenant_id${NC}"

    # Copy template .env file
    cp .env.example "$env_file"

    # Update tenant-specific settings using platform-specific sed command
    if [[ "$OS_TYPE" == "Darwin" ]]; then
        # macOS version
        sed -i '' "s/^TENANT_ID=.*/TENANT_ID=$tenant_id/" "$env_file"
        sed -i '' "s/^COLLECTION_NAME=.*/COLLECTION_NAME=legal_docs_$tenant_id/" "$env_file"
        sed -i '' "s/^API_PORT=.*/API_PORT=$api_port/" "$env_file"
        sed -i '' "s/^FRONTEND_PORT=.*/FRONTEND_PORT=$frontend_port/" "$env_file"
        sed -i '' "s/^HTTP_PORT=.*/HTTP_PORT=$http_port/" "$env_file"
        sed -i '' "s/^HTTPS_PORT=.*/HTTPS_PORT=$https_port/" "$env_file"

        # Configure document paths
        local docs_path="$PROJECT_DIR/tenants/$tenant_id/docs"
        mkdir -p "$docs_path/input"
        mkdir -p "$docs_path/output"
        mkdir -p "$docs_path/chunks"

        sed -i '' "s|^DOCS_ROOT=.*|DOCS_ROOT=$docs_path/output|" "$env_file"
        sed -i '' "s|^INPUT_DIR=.*|INPUT_DIR=$docs_path/input|" "$env_file"
        sed -i '' "s|^OUTPUT_DIR=.*|OUTPUT_DIR=$docs_path/output|" "$env_file"
        sed -i '' "s|^CHUNKS_DIR=.*|CHUNKS_DIR=$docs_path/chunks|" "$env_file"
    else
        # Linux version
        sed -i "s/^TENANT_ID=.*/TENANT_ID=$tenant_id/" "$env_file"
        sed -i "s/^COLLECTION_NAME=.*/COLLECTION_NAME=legal_docs_$tenant_id/" "$env_file"
        sed -i "s/^API_PORT=.*/API_PORT=$api_port/" "$env_file"
        sed -i "s/^FRONTEND_PORT=.*/FRONTEND_PORT=$frontend_port/" "$env_file"
        sed -i "s/^HTTP_PORT=.*/HTTP_PORT=$http_port/" "$env_file"
        sed -i "s/^HTTPS_PORT=.*/HTTPS_PORT=$https_port/" "$env_file"

        # Configure document paths
        local docs_path="$PROJECT_DIR/tenants/$tenant_id/docs"
        mkdir -p "$docs_path/input"
        mkdir -p "$docs_path/output"
        mkdir -p "$docs_path/chunks"

        sed -i "s|^DOCS_ROOT=.*|DOCS_ROOT=$docs_path/output|" "$env_file"
        sed -i "s|^INPUT_DIR=.*|INPUT_DIR=$docs_path/input|" "$env_file"
        sed -i "s|^OUTPUT_DIR=.*|OUTPUT_DIR=$docs_path/output|" "$env_file"
        sed -i "s|^CHUNKS_DIR=.*|CHUNKS_DIR=$docs_path/chunks|" "$env_file"
    fi

    echo -e "${GREEN}Environment file created: ${BLUE}$env_file${NC}"
    echo -e "${YELLOW}Important: You must update API keys in the environment file before deployment!${NC}"
    echo ""

    # Prompt user to edit the environment file
    read -p "Do you want to edit the environment file now? (y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ${EDITOR:-nano} "$env_file"
    fi

    return 0
}

# Function to deploy tenant
deploy_tenant() {
    local tenant_id=$1
    local env_file=".env.$tenant_id"
    local use_watch=${2:-false}

    echo -e "${BLUE}Deploying tenant: ${GREEN}$tenant_id${NC}"

    # Check if environment file exists
    if [ ! -f "$env_file" ]; then
        echo -e "${RED}Error: Environment file $env_file not found.${NC}"
        return 1
    fi

    # Deploy using docker-compose with build flag to ensure images are built with current configuration
    if [ "$use_watch" = true ]; then
        echo -e "${YELLOW}Deploying with watch mode enabled...${NC}"
        ENV_FILE="$env_file" docker-compose --env-file "$env_file" up -d --build
        echo -e "${GREEN}Starting watch mode...${NC}"
        ENV_FILE="$env_file" docker-compose --env-file "$env_file" watch
    else
        ENV_FILE="$env_file" docker-compose --env-file "$env_file" up -d --build
    fi

    echo -e "${GREEN}Tenant $tenant_id deployed successfully!${NC}"

    # Extract ports from env file
    local api_port=$(grep "^API_PORT=" "$env_file" | cut -d= -f2)
    local frontend_port=$(grep "^FRONTEND_PORT=" "$env_file" | cut -d= -f2)

    echo -e "${BLUE}Tenant endpoints:${NC}"
    echo -e "  API: ${GREEN}http://localhost:$api_port${NC}"
    echo -e "  Frontend: ${GREEN}http://localhost:$frontend_port${NC}"

    # Display logs command for troubleshooting
    echo -e "${YELLOW}To view logs:${NC}"
    echo -e "  API logs: ${BLUE}docker logs legal-search-api-$tenant_id${NC}"
    echo -e "  Frontend logs: ${BLUE}docker logs legal-search-frontend-$tenant_id${NC}"

    if [ "$use_watch" = true ]; then
        echo -e "${YELLOW}Watch mode is active. Code changes will be automatically synced and containers restarted.${NC}"
    fi

    return 0
}

# Function to list all tenants
list_tenants() {
    echo -e "${BLUE}Existing tenants:${NC}"

    local tenants=$(docker ps -a --format '{{.Names}}' | grep "legal-search-api-" | sed 's/legal-search-api-//')

    if [ -z "$tenants" ]; then
        echo -e "${YELLOW}No tenants deployed yet.${NC}"
        return 0
    fi

    echo -e "${GREEN}Tenant ID           Status          API Port    Frontend Port${NC}"
    echo -e "--------------------------------------------------------"

    for tenant in $tenants; do
        local status=$(docker ps --format '{{.Status}}' -f "name=legal-search-api-$tenant" | cut -d' ' -f1)
        if [ -z "$status" ]; then
            status="Stopped"
        fi

        local env_file=".env.$tenant"
        local api_port="N/A"
        local frontend_port="N/A"

        if [ -f "$env_file" ]; then
            api_port=$(grep "^API_PORT=" "$env_file" | cut -d= -f2)
            frontend_port=$(grep "^FRONTEND_PORT=" "$env_file" | cut -d= -f2)
        fi

        printf "%-20s %-15s %-11s %-15s\n" "$tenant" "$status" "$api_port" "$frontend_port"
    done

    return 0
}

# Function to stop a tenant
stop_tenant() {
    local tenant_id=$1
    local env_file=".env.$tenant_id"

    echo -e "${BLUE}Stopping tenant: ${GREEN}$tenant_id${NC}"

    # Check if environment file exists
    if [ ! -f "$env_file" ]; then
        echo -e "${RED}Error: Environment file $env_file not found.${NC}"
        return 1
    fi

    # Stop using docker-compose
    docker-compose --env-file "$env_file" down

    echo -e "${GREEN}Tenant $tenant_id stopped successfully!${NC}"

    return 0
}

# Function to delete a tenant
delete_tenant() {
    local tenant_id=$1
    local env_file=".env.$tenant_id"

    echo -e "${RED}WARNING: You are about to delete tenant: ${YELLOW}$tenant_id${NC}"
    echo -e "${RED}This will remove all containers, volumes, and data for this tenant!${NC}"

    read -p "Are you sure you want to continue? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}Deletion cancelled.${NC}"
        return 0
    fi

    # Stop tenant if running
    if tenant_exists "$tenant_id"; then
        docker-compose --env-file "$env_file" down -v
    fi

    # Remove tenant directory
    if [ -d "$PROJECT_DIR/tenants/$tenant_id" ]; then
        rm -rf "$PROJECT_DIR/tenants/$tenant_id"
    fi

    # Remove environment file
    if [ -f "$env_file" ]; then
        rm "$env_file"
    fi

    echo -e "${GREEN}Tenant $tenant_id deleted successfully!${NC}"

    return 0
}

# Main menu
show_menu() {
    echo -e "${BLUE}==================================================${NC}"
    echo -e "${BLUE}   Legal Search RAG - Multi-Tenant Management     ${NC}"
    echo -e "${BLUE}==================================================${NC}"
    echo ""
    echo -e "1. ${GREEN}Create and deploy new tenant${NC}"
    echo -e "2. ${BLUE}List existing tenants${NC}"
    echo -e "3. ${YELLOW}Stop a tenant${NC}"
    echo -e "4. ${RED}Delete a tenant${NC}"
    echo -e "5. ${GREEN}Start a stopped tenant${NC}"
    echo -e "0. ${RED}Exit${NC}"
    echo ""
    read -p "Enter your choice: " choice

    case $choice in
        1)
            echo ""
            read -p "Enter tenant ID: " tenant_id

            # Validate tenant ID
            if ! validate_tenant_id "$tenant_id"; then
                show_menu
                return
            fi

            # Check if tenant already exists
            if tenant_exists "$tenant_id"; then
                echo -e "${RED}Error: Tenant with ID '$tenant_id' already exists.${NC}"
                show_menu
                return
            fi

            # Find available ports
            read api_port frontend_port http_port https_port <<< $(find_available_ports $DEFAULT_BASE_PORT $DEFAULT_PORT_INCREMENT)

            # Create tenant environment file
            create_tenant_env "$tenant_id" "$api_port" "$frontend_port" "$http_port" "$https_port"

            # Prompt to deploy
            read -p "Do you want to deploy the tenant now? (y/n): " -n 1 -r
            echo ""
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                deploy_tenant "$tenant_id"
            fi
            ;;
        2)
            list_tenants
            ;;
        3)
            echo ""
            list_tenants
            echo ""
            read -p "Enter tenant ID to stop: " tenant_id

            # Validate tenant ID
            if ! validate_tenant_id "$tenant_id"; then
                show_menu
                return
            fi

            # Check if tenant exists
            if ! tenant_exists "$tenant_id"; then
                echo -e "${RED}Error: Tenant with ID '$tenant_id' does not exist.${NC}"
                show_menu
                return
            fi

            stop_tenant "$tenant_id"
            ;;
        4)
            echo ""
            list_tenants
            echo ""
            read -p "Enter tenant ID to delete: " tenant_id

            # Validate tenant ID
            if ! validate_tenant_id "$tenant_id"; then
                show_menu
                return
            fi

            # Delete tenant
            delete_tenant "$tenant_id"
            ;;
        5)
            echo ""
            list_tenants
            echo ""
            read -p "Enter tenant ID to start: " tenant_id

            # Validate tenant ID
            if ! validate_tenant_id "$tenant_id"; then
                show_menu
                return
            fi

            # Check if tenant exists
            if ! tenant_exists "$tenant_id"; then
                echo -e "${RED}Error: Tenant with ID '$tenant_id' does not exist.${NC}"
                show_menu
                return
            fi

            deploy_tenant "$tenant_id"
            ;;
        0)
            echo -e "${BLUE}Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid choice. Please try again.${NC}"
            ;;
    esac

    echo ""
    read -p "Press Enter to continue..."
    show_menu
}

# Start the menu
show_menu
