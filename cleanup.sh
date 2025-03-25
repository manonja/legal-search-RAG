#!/bin/bash

# Cleanup script for Legal Search RAG System
echo "Cleaning up Docker containers and images..."

# Stop and remove containers
echo "Stopping and removing containers..."
docker-compose -f shared/docker-compose.yml down --remove-orphans

# Remove Docker images
echo "Removing Docker images..."
docker rmi legal-search-rag-api:default legal-search-rag-frontend:default 2>/dev/null || true

# Remove Docker volumes
echo "Removing Docker volumes..."
docker volume rm legal_search_data_default 2>/dev/null || true

# Clean Docker build cache
echo "Cleaning Docker build cache..."
docker builder prune -f

# Clean frontend build artifacts
echo "Cleaning frontend build artifacts..."
rm -rf frontend/node_modules
rm -rf frontend/.next
rm -f frontend/.env.local

# Clean temporary files
echo "Cleaning temporary files..."
rm -f ./credentials/placeholder.json
rm -rf ./cache

echo "Cleanup complete! You can now run ./setup_credentials.sh and then ./setup.sh again."
echo ""
echo "Follow these steps:"
echo "1. Run ./setup_credentials.sh to configure your GCP credentials"
echo "2. Run ./setup.sh to start the system"
