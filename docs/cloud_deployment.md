# Cloud Deployment Guide for Legal Search RAG

This guide provides detailed instructions for deploying the Legal Search RAG system to cloud providers for production use.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Overview](#overview)
- [Deployment Options](#deployment-options)
- [Option 1: Render Deployment](#option-1-render-deployment)
- [Option 2: Railway Deployment](#option-2-railway-deployment)
- [S3 Document Storage](#s3-document-storage)
- [Environment Variables](#environment-variables)
- [Deployment Script](#deployment-script)
- [Manual Deployment Steps](#manual-deployment-steps)
- [Troubleshooting](#troubleshooting)
- [Monitoring](#monitoring)

## Prerequisites

Before deploying to the cloud, ensure you have:

- Git repository set up with your project
- AWS account (for S3 document storage)
- OpenAI API key
- Docker and Docker Compose installed locally
- Basic understanding of cloud services

## Overview

The Legal Search RAG system consists of three main components:

1. **Backend API**: FastAPI application that handles document search, RAG processing, and admin functionality
2. **Frontend**: Next.js application providing the user interface
3. **Document Storage**: Either local storage or cloud S3 storage

For cloud deployment, we recommend using S3 for document storage to ensure data persistence and accessibility.

## Deployment Options

We provide two recommended options for cloud deployment:

1. **Render**: Simple deployment with minimal configuration
2. **Railway**: More flexible deployment with better scaling options

Both options provide similar functionality, but the choice depends on your specific needs and preferences.

## Option 1: Render Deployment

[Render](https://render.com) provides a straightforward deployment process with automatic SSL certificates and containerized applications.

### Steps for Render Deployment

#### Backend API Deployment

1. Create a new account on Render if you don't have one
2. Click "New Web Service"
3. Connect your GitHub repository
4. Configure the service:
   - Name: `legal-search-api`
   - Environment: Docker
   - Branch: `main` (or your deployment branch)
   - Build Command: (leave as default)
   - Start Command: (leave as default)
5. Add environment variables from your `.env.deploy` file
6. Click "Create Web Service"

#### Frontend Deployment

1. Click "New Web Service"
2. Connect the same GitHub repository
3. Configure the service:
   - Name: `legal-search-frontend`
   - Root Directory: `nextjs-legal-search`
   - Environment: Node
   - Branch: `main` (or your deployment branch)
   - Build Command: `npm install && npm run build`
   - Start Command: `npm start`
4. Add environment variables:
   - `NEXT_PUBLIC_API_URL=https://your-api-service-url.onrender.com`
5. Click "Create Web Service"

## Option 2: Railway Deployment

[Railway](https://railway.app) offers a developer-friendly platform with better pricing for higher usage volumes.

### Steps for Railway Deployment

#### Using Railway CLI

1. Install Railway CLI:
   ```bash
   npm i -g @railway/cli
   ```

2. Login to Railway:
   ```bash
   railway login
   ```

3. Create a new project in Railway:
   ```bash
   railway init
   ```

4. Deploy the API:
   ```bash
   cd /path/to/legal-search-rag
   railway up
   ```

5. Deploy the frontend:
   ```bash
   cd /path/to/legal-search-rag/nextjs-legal-search
   railway up
   ```

6. Set environment variables in the Railway dashboard

#### Using Railway Dashboard

1. Create a new project in Railway
2. Connect your GitHub repository
3. Deploy both the API and frontend separately
4. Configure environment variables for each service
5. Link the services together

## S3 Document Storage

For production deployment, we strongly recommend using S3 for document storage:

1. Create an S3 bucket in your AWS account
2. Create an IAM user with S3 access permissions
3. Configure environment variables in your deployment:
   ```
   USE_S3_STORAGE=true
   S3_BUCKET_NAME=your-legal-docs-bucket
   S3_PREFIX=legal-search-data
   AWS_REGION=us-west-2
   AWS_ACCESS_KEY_ID=your_aws_access_key
   AWS_SECRET_ACCESS_KEY=your_aws_secret_key
   ```
4. Use the included script to sync documents to S3:
   ```bash
   python scripts/sync_to_s3.py
   ```

## Environment Variables

The following environment variables are required for cloud deployment:

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | API key for OpenAI | Yes |
| `USE_S3_STORAGE` | Enable S3 storage (true/false) | Yes for cloud |
| `S3_BUCKET_NAME` | AWS S3 bucket name | Yes for S3 |
| `AWS_REGION` | AWS region | Yes for S3 |
| `AWS_ACCESS_KEY_ID` | AWS access key | Yes for S3 |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | Yes for S3 |
| `NEXT_PUBLIC_API_URL` | URL for the API service | Yes for frontend |
| `ADMIN_API_KEY` | Key for admin dashboard access | Yes |
| `OPENAI_MONTHLY_BUDGET` | Budget limit for OpenAI API | Recommended |

## Deployment Script

We provide an automated deployment script that handles most of the setup process:

```bash
./scripts/deploy_to_cloud.sh [provider]
```

Where `provider` is either `render` or `railway` (defaults to `render`).

The script will:
1. Check prerequisites
2. Create a deployment environment file
3. Sync documents to S3 if enabled
4. Build Docker containers
5. Provide instructions for the final manual steps

## Manual Deployment Steps

After running the deployment script, some manual steps are still required:

1. Create services in your chosen cloud provider
2. Set environment variables from your `.env.deploy` file
3. Connect your GitHub repository
4. Configure build and start commands
5. Update the frontend's `NEXT_PUBLIC_API_URL` to point to your deployed API

## Troubleshooting

Common issues and solutions:

### API Connection Issues

- Ensure CORS settings are correctly configured
- Verify `NEXT_PUBLIC_API_URL` is set correctly in the frontend service
- Check that the API is running and accessible

### Document Storage Issues

- Verify S3 bucket permissions
- Check AWS credentials are correct
- Ensure documents were synced correctly using the sync script

### Build Failures

- Check Docker build logs for errors
- Ensure all dependencies are included in requirements.txt
- Verify environment variables are set correctly

## Monitoring

Once deployed, monitor your application using:

1. The admin dashboard at `/admin`
2. Cloud provider monitoring tools
3. AWS CloudWatch for S3 monitoring

We recommend setting up alerts for:
- API errors
- High usage spikes
- Cost thresholds exceeded
