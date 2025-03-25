#!/bin/bash

# Script to clean up and reorganize tenant directories
echo "Cleaning up tenant directories..."

# Create root tenants directory if it doesn't exist
mkdir -p tenants/default/docs

# Move documents from api/tenants to root tenants directory
if [ -d "api/tenants/docs" ]; then
  echo "Moving document directories from api/tenants/docs to tenants/default/docs..."

  # Move each subdirectory
  if [ -d "api/tenants/docs/chunks" ]; then
    cp -r api/tenants/docs/chunks tenants/default/docs/
    echo "Moved chunks directory"
  fi

  if [ -d "api/tenants/docs/input" ]; then
    cp -r api/tenants/docs/input tenants/default/docs/
    echo "Moved input directory"
  fi

  if [ -d "api/tenants/docs/output" ]; then
    cp -r api/tenants/docs/output tenants/default/docs/
    echo "Moved output directory"
  fi
fi

# Make sure default tenant has an env file
if [ ! -f "tenants/default/.env" ]; then
  echo "Creating default tenant environment file..."
  cat > "tenants/default/.env" << EOL
TENANT_ID=default
API_PORT=8000
FRONTEND_PORT=3000
ENV_FILE=$(pwd)/api/.env
EOL
fi

# No need to remove api/tenant directory as it contains the tenant_service.py file,
# which is an actual part of the API code, not a configuration directory

# Remove api/tenants directory as we've moved everything to root/tenants
if [ -d "api/tenants" ]; then
  echo "Removing api/tenants directory (moved to root)..."
  rm -rf api/tenants
fi

echo "Tenant directory cleanup complete!"
echo ""
echo "New structure:"
echo "- /tenants/             # Root tenants directory containing all tenant configurations"
echo "  - /default/           # Default tenant configuration"
echo "    - .env              # Environment variables for the default tenant"
echo "    - /docs/            # Documents for the default tenant"
echo "- /api/tenant/          # API module for tenant management code (not tenant data)"
echo ""
