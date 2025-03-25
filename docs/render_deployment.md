# Deploying Legal Search RAG to Render.com

This guide walks you through the process of deploying the Legal Search RAG system to Render.com with Google Cloud Storage integration.

## Prerequisites

Before you begin, ensure you have:

- A Render.com account
- A Google Cloud Platform (GCP) account with a project set up
- A GCS bucket created for storing documents
- GCP service account credentials (JSON file)
- Git repository with your Legal Search RAG code

## Step 1: Prepare GCP Credentials

1. Navigate to your project directory
2. Run the setup script to encode your GCP credentials:

```bash
./scripts/setup_gcp_credentials.sh /path/to/your-gcp-credentials.json
```

3. Copy the Base64 encoded string output by the script - you'll need this for Render.com

## Step 2: Deploy API Service to Render.com

1. Log in to your Render.com dashboard
2. Click "New" and select "Web Service"
3. Connect your Git repository
4. Configure the service:
   - **Name**: legal-search-api (or your preferred name)
   - **Environment**: Docker
   - **Branch**: main (or your deployment branch)
   - **Root Directory**: Leave empty if your Dockerfile is in the root
   - **Build Command**: Leave as default
   - **Start Command**: `mkdir -p /app/credentials && echo "$GCP_CREDENTIALS_BASE64" | base64 -d > /app/credentials/gcp-key.json && docker run -p $PORT:8000 legal-search-rag`

5. Set Environment Variables:
   - `USE_GCP_STORAGE`: true
   - `GCP_PROJECT_ID`: your-gcp-project-id
   - `GCS_BUCKET_NAME`: your-gcs-bucket-name
   - `GOOGLE_APPLICATION_CREDENTIALS`: /app/credentials/gcp-key.json
   - `GCP_CREDENTIALS_BASE64`: [Paste the encoded credentials from Step 1]
   - `INPUT_DIR`: /app/data/input
   - `OUTPUT_DIR`: /app/data/output
   - `GEMINI_API_KEY`: your-gemini-api-key
   - Any other environment variables from your .env file

6. Click "Create Web Service"

## Step 3: Deploy Frontend to Render.com

1. In your Render.com dashboard, click "New" and select "Web Service"
2. Connect your Git repository (same as before)
3. Configure the service:
   - **Name**: legal-search-frontend (or your preferred name)
   - **Environment**: Node
   - **Branch**: main (or your deployment branch)
   - **Root Directory**: nextjs-legal-search
   - **Build Command**: `npm install && npm run build`
   - **Start Command**: `npm start`

4. Set Environment Variables:
   - `NEXT_PUBLIC_API_URL`: https://your-api-service-url.onrender.com (URL of your API service)
   - Any other frontend environment variables

5. Click "Create Web Service"

## Step 4: Verify Deployment

1. Wait for both services to finish deploying
2. Test uploading documents to GCS:
   ```bash
   python scripts/upload_to_gcs.py /path/to/your/document.pdf
   ```
3. Access your frontend URL and verify that you can search and retrieve documents

## Troubleshooting

### GCP Credentials Issues

If you encounter issues with GCP credentials:

1. Verify the credentials are correctly encoded
2. Check if the credentials have the correct permissions
3. Examine the logs in your Render.com dashboard for errors

### Docker Build Issues

If Docker build fails:

1. Test your Docker build locally: `docker build -t legal-search-rag .`
2. Check if there are any dependency issues or missing files
3. Review Render.com build logs for specific errors

## Additional Notes

- For large documents, you may need to adjust the timeout settings in Render.com
- Consider setting up automatic deployments with GitHub Actions
- Regularly backup your GCS data
- Monitor your GCP usage to avoid unexpected costs
