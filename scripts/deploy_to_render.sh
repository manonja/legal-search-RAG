#!/bin/bash
# Script to deploy the Legal Search RAG to Render.com

set -e

# Check if render CLI is installed
if ! command -v render &> /dev/null; then
    echo "Error: Render CLI is not installed. Please install it first."
    echo "Visit: https://render.com/docs/cli"
    echo "You can install it with: npm install -g @render/cli"
    exit 1
fi

# Check if user is logged in to Render
if ! render whoami &> /dev/null; then
    echo "You are not logged in to Render. Please login:"
    render login
fi

# Check if the render.yaml file exists
if [ ! -f "render.yaml" ]; then
    echo "Error: render.yaml file not found in the current directory."
    exit 1
fi

# Deploy to Render
echo "Deploying to Render.com..."
render blueprint apply

echo "========================================================"
echo "Deployment initiated! Here's what's happening:"
echo "1. Render.com is building your services based on render.yaml"
echo "2. This may take several minutes to complete"
echo ""
echo "You can check the status of your deployment at:"
echo "https://dashboard.render.com"
echo ""
echo "Remember to configure your environment variables in the Render dashboard:"
echo "- OPENAI_API_KEY"
echo "- GOOGLE_API_KEY (if using Google Gemini)"
echo "- GCP_PROJECT_ID (if using GCP for storage)"
echo "- GCS_BUCKET_NAME (if using GCP for storage)"
echo ""
echo "For GCP integration, you'll need to upload your service account key"
echo "through the Render dashboard or set it as an environment secret."
echo "========================================================"
