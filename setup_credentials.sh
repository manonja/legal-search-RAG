#!/bin/bash

# Script to setup GCP credentials for the Legal Search RAG System
echo "Setting up GCP credentials..."

# Source path for credentials
SOURCE_CRED_PATH="/Users/manonjacquin/Downloads/legal-search-gcp-bucket.json"
TARGET_CRED_DIR="./credentials"
TARGET_CRED_PATH="$TARGET_CRED_DIR/gcp-credentials.json"

# Check if source credentials exist
if [ ! -f "$SOURCE_CRED_PATH" ]; then
  echo "Error: GCP credentials file not found at $SOURCE_CRED_PATH"
  exit 1
fi

# Create credentials directory if it doesn't exist
mkdir -p "$TARGET_CRED_DIR"

# Copy credentials to project directory
echo "Copying GCP credentials to project..."
cp "$SOURCE_CRED_PATH" "$TARGET_CRED_PATH"

# Make sure permissions are correct
chmod 600 "$TARGET_CRED_PATH"

# Update the default tenant environment file
TENANT_ENV_FILE="./tenants/default/.env"

# Check if tenant env file exists
if [ -f "$TENANT_ENV_FILE" ]; then
  # Remove old GCP_CREDENTIALS line if exists
  grep -v "GCP_CREDENTIALS=" "$TENANT_ENV_FILE" > "$TENANT_ENV_FILE.tmp"
  mv "$TENANT_ENV_FILE.tmp" "$TENANT_ENV_FILE"

  # Add the new path
  echo "GCP_CREDENTIALS=$TARGET_CRED_PATH" >> "$TENANT_ENV_FILE"
  echo "Updated tenant environment file with credentials path"
else
  echo "Warning: Tenant environment file not found at $TENANT_ENV_FILE"
fi

# Display setup instructions
echo ""
echo "GCP credentials have been set up successfully!"
echo ""
echo "For this terminal session, run:"
echo "  export GOOGLE_APPLICATION_CREDENTIALS=\"$TARGET_CRED_PATH\""
echo ""
echo "To make this permanent for your shell, add this line to your ~/.zshrc file:"
echo "  export GOOGLE_APPLICATION_CREDENTIALS=\"$(pwd)/$TARGET_CRED_PATH\""
echo ""
echo "Now run ./setup.sh to start the system with the configured credentials"
