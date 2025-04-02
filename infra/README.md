# GCP Docker Registry with Pulumi

This project sets up a Docker registry in Google Cloud Platform's Artifact Registry using Pulumi.

## Configuration

The Docker registry will be named `maja-{environment}` where `{environment}` is your Pulumi stack name (e.g., dev, staging, prod).

## Prerequisites

1. Google Cloud account and project
2. `gcloud` CLI configured
3. Pulumi CLI installed
4. Python 3.12+

## Deployment

```bash
# Select or create a stack (environment)
pulumi stack select dev  # or create a new one: pulumi stack init [name]

# Deploy the infrastructure
pulumi up
```

## Features

- Automatically enables required Google Cloud APIs:
  - artifactregistry.googleapis.com
  - containerregistry.googleapis.com
  - storage.googleapis.com
  - iam.googleapis.com
- Creates a Docker repository in Artifact Registry with environment-specific naming
- Provides example commands for authentication and usage

## Using the Docker Registry

After deployment, you'll see outputs for `repository_id` and `repository_url`. To use the registry:

1. Authenticate to GCP and the Artifact Registry:
   ```bash
   gcloud auth login
   gcloud auth configure-docker us-central1-docker.pkg.dev
   ```

2. Tag and push your Docker images:
   ```bash
   docker tag your-image:tag us-central1-docker.pkg.dev/your-project-id/maja-dev/your-image:tag
   docker push us-central1-docker.pkg.dev/your-project-id/maja-dev/your-image:tag
   ```

3. Pull images:
   ```bash
   docker pull us-central1-docker.pkg.dev/your-project-id/maja-dev/your-image:tag
   ```

## IAM Permissions

By default, you'll need the following roles to push/pull images:
- Artifact Registry Writer (`roles/artifactregistry.writer`) to push images
- Artifact Registry Reader (`roles/artifactregistry.reader`) to pull images

You may need to grant these roles to service accounts or other users as needed.

## Troubleshooting

If you encounter any errors related to APIs not being enabled, the code should automatically enable them for you. However, it may take a few minutes for the API activation to propagate through Google's systems. If you continue to see errors, you can try running `pulumi up` again after a few minutes.
