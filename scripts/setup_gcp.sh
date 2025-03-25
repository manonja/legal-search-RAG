#!/bin/bash
# Script to set up GCP integration for the Legal Search RAG system
# This script creates a GCP service account with necessary permissions
# and configures the application to use GCP for storage

set -e

# Default GCP project name if not specified
DEFAULT_PROJECT_NAME="legal-search-$(date +%s | md5sum | head -c 6)"
DEFAULT_BUCKET_NAME="legal-docs-$(date +%s | md5sum | head -c 6)"

# Ensure gcloud CLI is installed
if ! command -v gcloud &> /dev/null; then
    echo "Error: gcloud CLI is not installed. Please install it first."
    echo "Visit: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check if user is logged in to gcloud
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q '@'; then
    echo "You are not logged in to Google Cloud. Please login:"
    gcloud auth login
fi

# Ask for project name
read -p "Enter GCP project name [$DEFAULT_PROJECT_NAME]: " PROJECT_NAME
PROJECT_NAME=${PROJECT_NAME:-$DEFAULT_PROJECT_NAME}

# Create a new GCP project
echo "Creating GCP project: $PROJECT_NAME"
gcloud projects create $PROJECT_NAME --name="Legal Search RAG"

# Set the new project as the active project
gcloud config set project $PROJECT_NAME

# Enable required APIs
echo "Enabling required APIs..."
gcloud services enable storage-api.googleapis.com
gcloud services enable storage-component.googleapis.com
gcloud services enable iam.googleapis.com

# Create a service account
SA_NAME="legal-search-sa"
SA_EMAIL="$SA_NAME@$PROJECT_NAME.iam.gserviceaccount.com"
echo "Creating service account: $SA_NAME"
gcloud iam service-accounts create $SA_NAME \
    --display-name="Legal Search RAG Service Account"

# Create a GCS bucket
read -p "Enter GCS bucket name [$DEFAULT_BUCKET_NAME]: " BUCKET_NAME
BUCKET_NAME=${BUCKET_NAME:-$DEFAULT_BUCKET_NAME}
echo "Creating GCS bucket: $BUCKET_NAME"
gcloud storage buckets create gs://$BUCKET_NAME --location=us-west1

# Grant permissions to the service account
echo "Granting permissions to service account..."
gcloud storage buckets add-iam-policy-binding gs://$BUCKET_NAME \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/storage.objectAdmin"

# Create a key for the service account
echo "Creating service account key..."
KEY_FILE="credentials/gcp-key.json"
mkdir -p credentials
gcloud iam service-accounts keys create $KEY_FILE \
    --iam-account=$SA_EMAIL

# Update environment variables
echo "Updating environment variables..."
if [ -f "api/.env" ]; then
    # Backup existing .env file
    cp api/.env api/.env.backup

    # Update environment variables
    sed -i '' 's/USE_GCP_STORAGE=.*/USE_GCP_STORAGE=true/' api/.env
    sed -i '' "s/GCP_PROJECT_ID=.*/GCP_PROJECT_ID=$PROJECT_NAME/" api/.env
    sed -i '' "s/GCS_BUCKET_NAME=.*/GCS_BUCKET_NAME=$BUCKET_NAME/" api/.env
    sed -i '' "s|GOOGLE_APPLICATION_CREDENTIALS=.*|GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/gcp-key.json|" api/.env
else
    echo "Warning: .env file not found. Please update environment variables manually."
fi

echo "========================================================"
echo "GCP setup complete! Here's what was done:"
echo "1. Created project: $PROJECT_NAME"
echo "2. Created service account: $SA_NAME"
echo "3. Created GCS bucket: $BUCKET_NAME"
echo "4. Created service account key at: $KEY_FILE"
echo "5. Updated environment variables in .env file"
echo ""
echo "Next steps:"
echo "1. Make sure to include the following in your .env file:"
echo "   USE_GCP_STORAGE=true"
echo "   GCP_PROJECT_ID=$PROJECT_NAME"
echo "   GCS_BUCKET_NAME=$BUCKET_NAME"
echo "   GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/gcp-key.json"
echo ""
echo "2. In your deployment, make sure to mount the key file"
echo "   at /app/credentials/gcp-key.json"
echo "========================================================"
