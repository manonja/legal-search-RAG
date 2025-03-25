#!/bin/bash
set -e

# Setup script for Legal Search RAG System
echo "Setting up Legal Search RAG System..."

# Create .env file if it doesn't exist
if [ ! -f ./api/.env ]; then
    echo "Creating .env file..."
    cp ./api/.env.example ./api/.env
    echo "Please edit the .env file with your API keys if needed."
else
    echo ".env file already exists"
fi

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p ./tenants/default/docs
mkdir -p ./credentials

# Check for GCP credentials
echo "Checking GCP credentials..."
if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "GOOGLE_APPLICATION_CREDENTIALS environment variable is not set."

    # Search for credentials in the credentials directory
    CREDENTIALS_DIR="./credentials"
    if [ -d "$CREDENTIALS_DIR" ]; then
        # Look for any JSON file that's not a placeholder
        for cred_file in "$CREDENTIALS_DIR"/*.json; do
            if [ -f "$cred_file" ] && [ "$cred_file" != "$CREDENTIALS_DIR/placeholder.json" ]; then
                # Found a credential file, use it
                export GOOGLE_APPLICATION_CREDENTIALS="$cred_file"
                export GCP_CREDENTIALS="$cred_file"
                echo "Found credentials file: $cred_file"
                echo "Using it for this session."
                break
            fi
        done
    fi

    # If still not set, create a placeholder
    if [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
        echo ""
        echo "=== GCP Credentials Setup ==="
        echo "For GCP features, place your service account key file in the ./credentials directory."
        echo ""
        echo "For now, system will run without GCP integration."
        echo "Creating a placeholder file for Docker volume mounting..."

        # Create a placeholder credentials file
        mkdir -p ./credentials
        echo "{}" > ./credentials/placeholder.json
        export GCP_CREDENTIALS="./credentials/placeholder.json"
    fi
else
    echo "GOOGLE_APPLICATION_CREDENTIALS is set to: $GOOGLE_APPLICATION_CREDENTIALS"
    export GCP_CREDENTIALS="$GOOGLE_APPLICATION_CREDENTIALS"
fi

# Add credentials path to tenant env file
echo "GCP_CREDENTIALS=$GCP_CREDENTIALS" > ./tenants/default/.env

# Create .env.local file for frontend if it doesn't exist
echo "Creating frontend environment file..."
mkdir -p ./frontend
cat > "./frontend/.env.local" << EOL
NEXT_PUBLIC_API_URL=http://localhost:8000
EOL

# Pull the latest Node and Python images first
echo "Pulling base images..."
docker pull node:18-alpine
docker pull python:3.10-slim

# Clean up any previous builds
echo "Cleaning up previous builds..."
docker-compose -f shared/docker-compose.yml down || true

# Build Docker images
echo "Building Docker images (this may take a few minutes)..."
API_PORT=8000 FRONTEND_PORT=3000 docker-compose -f shared/docker-compose.yml build --no-cache

# Start Docker containers with explicit port settings
echo "Starting Docker containers..."
export API_PORT=8000
export FRONTEND_PORT=3000
docker-compose -f shared/docker-compose.yml up -d

# Check if containers are running
echo "Checking container status..."
sleep 5
docker ps | grep "legal-search"

# Provide info on next steps
echo "Setup complete! Your services should be running at:"
echo "- Frontend: http://localhost:3000"
echo "- API: http://localhost:8000"
echo ""
echo "To test the API directly, try:"
echo "curl http://localhost:8000/api/health"
echo ""
echo "To use the search functionality, visit:"
echo "http://localhost:3000/search"
echo ""
echo "To view container logs:"
echo "docker logs legal-search-api-default"
echo "docker logs legal-search-frontend-default"
