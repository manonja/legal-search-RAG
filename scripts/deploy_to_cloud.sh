#!/bin/bash
# Deployment script for Legal Search RAG to cloud providers
set -e

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROVIDER=${1:-"render"}
ENV_FILE=".env.deploy"
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo -e "${BLUE}Legal Search RAG Cloud Deployment Tool${NC}"
echo "========================================="
echo -e "${YELLOW}Provider:${NC} $PROVIDER"
echo -e "${YELLOW}Project:${NC} $PROJECT_DIR"
echo

# Check prerequisites
check_prerequisites() {
    echo -e "${BLUE}Checking prerequisites...${NC}"

    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Python 3 is required but not installed${NC}"
        exit 1
    fi

    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Docker is required but not installed${NC}"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}Docker Compose is required but not installed${NC}"
        exit 1
    fi

    if [ ! -f "$PROJECT_DIR/.env" ]; then
        echo -e "${RED}.env file not found. Please create one based on .env.example${NC}"
        exit 1
    fi

    echo -e "${GREEN}All prerequisites are satisfied${NC}"
}

# Prepare deployment environment file
prepare_env_file() {
    echo -e "${BLUE}Preparing deployment environment...${NC}"

    # Copy base .env file
    cp "$PROJECT_DIR/.env" "$PROJECT_DIR/$ENV_FILE"

    # Check if S3 storage is configured
    USE_S3=$(grep -i "^USE_S3_STORAGE=true" "$PROJECT_DIR/$ENV_FILE" || echo "")

    if [ -z "$USE_S3" ]; then
        echo -e "${YELLOW}S3 storage is not enabled in your .env file${NC}"
        read -p "Do you want to enable S3 storage for this deployment? (y/n) " -n 1 -r
        echo

        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "USE_S3_STORAGE=true" >> "$PROJECT_DIR/$ENV_FILE"

            read -p "Enter your S3 bucket name: " S3_BUCKET
            echo "S3_BUCKET_NAME=$S3_BUCKET" >> "$PROJECT_DIR/$ENV_FILE"

            read -p "Enter AWS region (default: us-west-2): " AWS_REGION
            AWS_REGION=${AWS_REGION:-"us-west-2"}
            echo "AWS_REGION=$AWS_REGION" >> "$PROJECT_DIR/$ENV_FILE"

            read -p "Enter AWS access key ID: " AWS_ACCESS_KEY
            echo "AWS_ACCESS_KEY_ID=$AWS_ACCESS_KEY" >> "$PROJECT_DIR/$ENV_FILE"

            read -p "Enter AWS secret access key: " AWS_SECRET_KEY
            echo "AWS_SECRET_ACCESS_KEY=$AWS_SECRET_KEY" >> "$PROJECT_DIR/$ENV_FILE"

            USE_S3=true
        fi
    else
        USE_S3=true
        echo -e "${GREEN}S3 storage is already configured${NC}"
    fi

    # Set additional configuration for cloud deployment
    echo "NEXT_PUBLIC_API_URL=https://YOUR-API-DOMAIN-HERE" >> "$PROJECT_DIR/$ENV_FILE"

    echo -e "${GREEN}Deployment environment prepared: $ENV_FILE${NC}"
    return 0
}

# Sync documents to S3 if enabled
sync_documents() {
    if [ "$USE_S3" = true ]; then
        echo -e "${BLUE}Syncing documents to S3...${NC}"

        # Activate Python environment
        cd "$PROJECT_DIR"

        # Sync documents using the sync script
        python3 scripts/sync_to_s3.py --verbose

        if [ $? -eq 0 ]; then
            echo -e "${GREEN}Documents synced to S3 successfully${NC}"
        else
            echo -e "${RED}Failed to sync documents to S3${NC}"
            echo -e "${YELLOW}Please check S3 configuration and try again${NC}"
            exit 1
        fi
    else
        echo -e "${YELLOW}Skipping document sync to S3 (not enabled)${NC}"
    fi
}

# Build Docker containers
build_containers() {
    echo -e "${BLUE}Building Docker containers...${NC}"

    cd "$PROJECT_DIR"
    docker-compose -f docker-compose.yml build

    echo -e "${GREEN}Docker containers built successfully${NC}"
}

# Handle provider-specific deployment
deploy_to_provider() {
    case "$PROVIDER" in
        render)
            deploy_to_render
            ;;
        railway)
            deploy_to_railway
            ;;
        *)
            echo -e "${RED}Unsupported provider: $PROVIDER${NC}"
            echo -e "${YELLOW}Supported providers: render, railway${NC}"
            exit 1
            ;;
    esac
}

# Deploy to Render
deploy_to_render() {
    echo -e "${BLUE}Deploying to Render...${NC}"

    # Instructions for manual deployment to Render
    echo -e "${YELLOW}To deploy to Render:${NC}"
    echo "1. Create a new Web Service in Render"
    echo "2. Connect your GitHub repository"
    echo "3. Use the following settings:"
    echo "   - Environment: Docker"
    echo "   - Build Command: docker build -t legal-search-rag ."
    echo "   - Start Command: docker run -p \$PORT:8000 legal-search-rag"
    echo "4. Add the environment variables from $ENV_FILE"
    echo
    echo -e "${YELLOW}To deploy the frontend:${NC}"
    echo "1. Create a new Web Service in Render"
    echo "2. Connect your GitHub repository with the path /nextjs-legal-search"
    echo "3. Use the following settings:"
    echo "   - Environment: Node"
    echo "   - Build Command: npm install && npm run build"
    echo "   - Start Command: npm start"
    echo "4. Add the environment variables:"
    echo "   - NEXT_PUBLIC_API_URL=https://your-api-service-url.onrender.com"

    echo -e "${GREEN}Render deployment instructions displayed${NC}"
}

# Deploy to Railway
deploy_to_railway() {
    echo -e "${BLUE}Deploying to Railway...${NC}"

    # Check if railway CLI is installed
    if ! command -v railway &> /dev/null; then
        echo -e "${YELLOW}Railway CLI not found. Installing...${NC}"
        npm i -g @railway/cli
    fi

    # Instructions for manual deployment to Railway
    echo -e "${YELLOW}To deploy to Railway:${NC}"
    echo "1. Login to Railway:"
    echo "   railway login"
    echo "2. Link your project:"
    echo "   railway link"
    echo "3. Deploy the API:"
    echo "   cd $PROJECT_DIR && railway up"
    echo "4. Deploy the frontend:"
    echo "   cd $PROJECT_DIR/nextjs-legal-search && railway up"
    echo "5. Set the environment variables from $ENV_FILE in Railway dashboard"

    echo -e "${GREEN}Railway deployment instructions displayed${NC}"
}

# Display summary and next steps
display_summary() {
    echo -e "${BLUE}Deployment Summary${NC}"
    echo "======================="
    echo -e "${GREEN}✓${NC} Prerequisites checked"
    echo -e "${GREEN}✓${NC} Environment prepared: $ENV_FILE"

    if [ "$USE_S3" = true ]; then
        echo -e "${GREEN}✓${NC} Documents synced to S3"
    else
        echo -e "${YELLOW}!${NC} Documents not synced (S3 disabled)"
    fi

    echo -e "${GREEN}✓${NC} Docker containers built"
    echo -e "${YELLOW}!${NC} Manual steps required to complete deployment"

    echo
    echo -e "${BLUE}Next Steps:${NC}"
    echo "1. Follow the provider-specific instructions above"
    echo "2. Update the NEXT_PUBLIC_API_URL in your frontend environment"
    echo "3. Test your deployment by accessing the frontend URL"
    echo
    echo -e "${GREEN}Thank you for using the Legal Search RAG deployment tool!${NC}"
}

# Main execution flow
main() {
    check_prerequisites
    prepare_env_file
    sync_documents
    build_containers
    deploy_to_provider
    display_summary
}

# Run the main function
main
