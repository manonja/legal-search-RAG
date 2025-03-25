# Cloud Deployment Guide for Legal Search RAG

This guide provides detailed instructions for deploying the Legal Search RAG system to cloud providers with both AWS S3 and Google Cloud Storage (GCS) integration.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Storage Options](#storage-options)
- [AWS S3 Integration](#aws-s3-integration)
- [Google Cloud Storage Integration](#google-cloud-storage-integration)
- [Deployment Options](#deployment-options)
- [Custom Docker Deployment](#custom-docker-deployment)
- [Monitoring and Maintenance](#monitoring-and-maintenance)

## Prerequisites

Before deploying to the cloud, ensure you have:

- A complete and tested local setup
- Access to cloud provider accounts (AWS, GCP, Render.com, or Railway)
- API keys and credentials for all services
- Your legal document corpus

## Storage Options

The Legal Search RAG system supports three storage options:

1. **Local Storage**: Documents and embeddings stored locally (default)
2. **AWS S3**: Documents stored in S3 buckets
3. **Google Cloud Storage**: Documents stored in GCS buckets

You can use one or both cloud storage options simultaneously.

## AWS S3 Integration

### Setting Up AWS S3

1. Create an AWS account if you don't have one
2. Create an S3 bucket for your documents
3. Create an IAM user with programmatic access and S3 permissions
4. Note your AWS access key ID and secret access key

### Configure AWS S3 for Local Development

1. Configure your environment with AWS credentials:
   ```bash
   ./scripts/setup_local_s3.sh
   ```

2. Follow the prompts to add your:
   - AWS access key ID
   - AWS secret access key
   - S3 bucket name
   - AWS region

3. Sync your documents to S3:
   ```bash
   python scripts/sync_to_s3.py
   ```

## Google Cloud Storage Integration

### Setting Up Google Cloud Storage

1. Create a GCP account if you don't have one
2. Create a new GCP project or select an existing one
3. Enable the Cloud Storage API
4. Create a GCS bucket for your documents
5. Create a service account with Storage Admin permissions
6. Download the service account credentials JSON file

### Configure GCP for Local Development

1. Configure your environment with GCP credentials:
   ```bash
   ./scripts/setup_local_gcp.sh /path/to/gcp-credentials.json
   ```

2. Follow the prompts to confirm:
   - GCP project ID (extracted from credentials)
   - GCS bucket name

3. Upload test documents to GCS:
   ```bash
   python scripts/upload_to_gcs.py /path/to/document.pdf
   ```

4. List uploaded documents:
   ```bash
   python scripts/upload_to_gcs.py --list
   ```

## Deployment Options

### Render.com

Render.com provides an easy-to-use platform for deploying containerized applications.

Follow our dedicated guide:
- [Render.com Deployment Guide](render_deployment.md)

### Railway

Railway is a developer-friendly platform with flexible scaling options.

1. Install the Railway CLI:
   ```bash
   npm i -g @railway/cli
   ```

2. Run our deployment script:
   ```bash
   ./scripts/deploy_to_cloud.sh railway
   ```

3. Follow the interactive prompts to:
   - Log in to Railway
   - Select your project
   - Configure environment variables
   - Deploy the application

## Custom Docker Deployment

For custom cloud deployments, use our Docker Compose production configuration:

1. Configure your `.env.production` file with cloud credentials
2. Deploy using:
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.production.yml up -d
   ```

## Monitoring and Maintenance

### Monitoring Document Processing

Monitor document processing in the cloud:

1. Check processing logs:
   ```bash
   docker-compose logs -f api
   ```

2. View uploaded documents:
   - For S3: `python scripts/list_s3_docs.py`
   - For GCS: `python scripts/upload_to_gcs.py --list`

### Cost Management

1. Monitor your usage of:
   - Cloud storage (S3/GCS)
   - OpenAI API
   - Google Gemini API
   - Cloud hosting provider

2. Set up alerts for unexpected cost increases

3. Consider implementing database backups for your embeddings

### Security Considerations

1. Ensure your API keys and credentials are stored securely
2. Use environment variables for sensitive information
3. Consider implementing API rate limiting and authentication
4. Regularly rotate credentials and API keys

## Troubleshooting

### Common Issues

1. **Storage Access Errors**
   - Check permissions on your S3 bucket or GCS bucket
   - Verify your credentials are correctly set in environment variables

2. **Document Processing Failures**
   - Check logs for specific error messages
   - Ensure document format is supported (PDF or DOCX)
   - Verify API keys for Gemini are valid

3. **Deployment Failures**
   - Check Docker build logs
   - Verify all environment variables are correctly set
   - Ensure all dependencies are properly installed

For additional help, please consult our troubleshooting documentation or open an issue on GitHub.
