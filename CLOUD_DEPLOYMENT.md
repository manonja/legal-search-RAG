# Cloud Deployment Guide

This guide provides detailed instructions for deploying the Legal Search RAG system to cloud platforms.

## Render.com Deployment

Render.com is a unified cloud for building and running apps and websites with free TLS certificates, a global CDN, DDoS protection, private networks, and auto deploys from Git.

### Prerequisites
- A Render.com account
- Render CLI installed: `npm install -g @render/cli`
- Git repository with your project

### Deployment Steps

1. **Install Render CLI**
   ```bash
   npm install -g @render/cli
   ```

2. **Login to Render**
   ```bash
   render login
   ```

3. **Prepare GCP Integration (Optional)**
   If you want to use Google Cloud Storage for document storage:
   ```bash
   ./scripts/setup_gcp.sh
   ```
   This script will:
   - Create a new GCP project
   - Enable required APIs
   - Create a service account
   - Create a storage bucket
   - Generate a key file
   - Update your .env file

4. **Deploy to Render.com**
   ```bash
   ./scripts/deploy_to_render.sh
   ```
   This uses the `render.yaml` blueprint in your project to create:
   - The API service (legal-search-api)
   - The frontend service (legal-search-frontend)
   - Persistent disk for ChromaDB storage

5. **Configure Environment Variables**
   After deployment, visit the Render dashboard to set these environment variables:
   - `OPENAI_API_KEY` - Your OpenAI API key
   - `GOOGLE_API_KEY` - Your Google API key (if using Gemini)
   - `GCP_PROJECT_ID` - Your GCP project ID (if using GCP storage)
   - `GCS_BUCKET_NAME` - Your GCS bucket name (if using GCP storage)
   - `USE_GCP_STORAGE` - Set to 'true' if using GCP

6. **Upload GCP Service Account Key (Optional)**
   If using GCP storage:
   - Go to the Render dashboard > legal-search-api > Environment
   - Under "Secret Files" add your GCP key file
   - Path: `/app/credentials/gcp-key.json`
   - Content: Copy-paste your key file content

7. **Process Documents**
   You'll need to process your documents after deployment:
   - Upload documents via the admin interface
   - Or use GCP bucket to upload directly to cloud storage

## Other Cloud Providers

### AWS Elastic Beanstalk

1. Update the Docker configuration:
   ```bash
   cp shared/docker-compose.yml Dockerrun.aws.json
   ```

2. Follow AWS Elastic Beanstalk deployment guides for Docker environments

### Google Cloud Run

The API service can be deployed to Cloud Run:

1. Build the API container:
   ```bash
   cd api
   gcloud builds submit --tag gcr.io/[PROJECT_ID]/legal-search-api
   ```

2. Deploy to Cloud Run:
   ```bash
   gcloud run deploy legal-search-api \
     --image gcr.io/[PROJECT_ID]/legal-search-api \
     --platform managed
   ```

## Troubleshooting

### ChromaDB Storage Issues
- Ensure the persistent disk is properly mounted
- Check disk permissions are correct
- Verify environment variables for storage paths

### API Connection Problems
- Check CORS settings in the API
- Verify the frontend is configured with the correct API URL
- Ensure network rules allow communications between services

### GCP Authentication Issues
- Verify the key file exists and is correct
- Ensure service account has proper permissions
- Check that required APIs are enabled
