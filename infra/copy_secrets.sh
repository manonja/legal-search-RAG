#!/bin/bash

# List all secrets from the source project
SOURCE_PROJECT="maja-dev"
TARGET_PROJECT="maja-prod"

# Get list of all secrets from source project
echo "Listing secrets from $SOURCE_PROJECT..."
secrets=$(gcloud secrets list --project=$SOURCE_PROJECT --format="value(name)")

# Loop through each secret and copy it to the target project
for secret_name in $secrets; do
  echo "Processing secret: $secret_name"

  # Get the latest version of the secret
  echo "Accessing latest version from source project..."

  # Copy the secret to the target project
  echo "Creating secret in target project..."
  gcloud secrets versions access latest --secret=$secret_name --project=$SOURCE_PROJECT | \
    gcloud secrets create $secret_name --project=$TARGET_PROJECT --data-file=-

  echo "Secret $secret_name copied successfully."
done

echo "All secrets have been copied from $SOURCE_PROJECT to $TARGET_PROJECT."
