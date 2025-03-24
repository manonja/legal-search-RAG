# Multi-Tenant Deployment Guide

This guide explains how to deploy and manage multiple instances of the Legal Search RAG system, with each instance serving a different tenant (user) with their own isolated data.

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Prerequisites](#prerequisites)
3. [Deployment Instructions](#deployment-instructions)
4. [Document Processing](#document-processing)
5. [Using the RAG System](#using-the-rag-system)
6. [Managing Tenants](#managing-tenants)
7. [Troubleshooting](#troubleshooting)
8. [Security Considerations](#security-considerations)

## Architecture Overview

The multi-tenant deployment uses Docker containers to isolate each tenant's services:

1. **API Container**: FastAPI backend for handling search queries and document processing
2. **Frontend Container**: Next.js frontend for the user interface
3. **Nginx Container**: Reverse proxy for routing requests

Each tenant has:
- Isolated vector database (ChromaDB)
- Separate document storage
- Independent usage tracking
- Unique ports for API and frontend access

## Prerequisites

- Docker and Docker Compose installed
- Bash shell environment
- Network connectivity for the required ports
- API keys for OpenAI and Google (for Gemini model)

## Deployment Instructions

### Quick Start: Deploying a New Tenant Instance

For beginners, we recommend using our automated quick start script which guides you through the entire process:

```bash
./scripts/quick_start.sh
```

This script will:
1. Check prerequisites
2. Guide you through creating a new tenant with the correct configuration
3. Help you add documents
4. Process the documents
5. Provide access URLs for your system

For more experienced users who prefer manual control, follow these steps:

1. **Clone the repository** (if you haven't already):
   ```bash
   git clone https://github.com/your-username/legal-search-RAG.git
   cd legal-search-RAG
   ```

2. **Run the deployment script**:
   ```bash
   ./scripts/deploy_tenant.sh
   ```

3. **Create a new tenant**:
   - Select option `1` from the menu
   - Enter a tenant ID (e.g., `tenant1`) when prompted
   - The script will find available ports and create a configuration file

4. **Configure the tenant**:
   - When prompted, edit the environment file to add your API keys:
     ```
     GOOGLE_API_KEY=your_google_api_key_here
     OPENAI_API_KEY=your_openai_api_key_here
     ```
   - Save and exit the editor

5. **Deploy the tenant**:
   - Choose `y` when asked if you want to deploy now
   - The script will build and start the Docker containers
   - Note the API and frontend URLs displayed after deployment

### Manual Deployment

If you prefer to deploy tenants manually, follow these steps:

1. **Create Tenant Environment File**:
   ```bash
   cp .env.example .env.tenant_name
   ```

2. **Edit the environment file** to add your API keys and configure ports.

3. **Deploy Tenant**:
   ```bash
   ENV_FILE=".env.tenant_name" docker-compose --env-file .env.tenant_name up -d --build
   ```

## Document Processing

### Adding Documents

We provide several options for adding documents to your tenant:

#### Option 1: Using the Interactive Helper Script (Recommended)

```bash
./scripts/add_documents.sh tenant_name
```

This script provides a user-friendly interface to:
- Select files using a file picker (on macOS)
- Copy files from a directory
- Guide you through manual file copying
- Automatically process the documents after they're added

#### Option 2: Manual File Copying

1. **Prepare your documents**:
   - Gather the legal documents you want to add to the system (PDF or DOCX format)
   - Create the input directory (if needed):
     ```bash
     mkdir -p tenants/tenant_name/docs/input
     ```

2. **Copy documents to the tenant's input directory**:
   ```bash
   cp /path/to/your/documents/*.pdf tenants/tenant_name/docs/input/
   ```

### Processing Documents

1. **Run the document processing script**:
   ```bash
   ./scripts/process_tenant_docs.sh tenant_name
   ```

2. **The script will perform the following steps**:
   - Extract text from PDFs/DOCXs using PyMuPDF and python-docx
   - Enhance document formatting using the Gemini model
   - Split documents into overlapping chunks for better retrieval
   - Generate embeddings using OpenAI's embedding model
   - Store embeddings in a tenant-specific ChromaDB collection

3. **Monitor the output** to ensure all steps complete successfully.

### Document Processing Flow Details

The RAG system processes documents in three stages:

1. **Text Extraction** (`process_docs.py`):
   - Reads PDF/DOCX files from the input directory
   - Extracts raw text using PyMuPDF or python-docx
   - Uses Gemini to improve formatting and structure
   - Saves as text files in `tenants/tenant_name/docs/output/`

2. **Document Chunking** (`chunk.py`):
   - Splits documents into smaller, overlapping chunks (512 chars with 50 char overlap)
   - Uses LangChain's RecursiveCharacterTextSplitter
   - Saves chunks with markers in `tenants/tenant_name/docs/chunks/`

3. **Embedding Generation** (`embeddings.py`):
   - Generates vector embeddings for each chunk using OpenAI
   - Stores embeddings in ChromaDB
   - Files are saved in `cache/chroma/tenant_name/`

## Using the RAG System

### Accessing the Frontend

1. **Open your browser** and navigate to the tenant's frontend URL:
   ```
   http://localhost:[FRONTEND_PORT]
   ```
   (The port number is shown after deployment)

2. **Use the search interface** to query your documents:
   - Type natural language questions about your legal documents
   - View search results with highlighted source documents
   - Explore document metadata and access original files

### Using the API Directly

1. **Query the search endpoint**:
   ```bash
   curl -X POST http://localhost:[API_PORT]/api/search \
     -H "Content-Type: application/json" \
     -d '{"query_text": "What are the requirements for termination?"}'
   ```

2. **Use the RAG endpoint** for enhanced answers:
   ```bash
   curl -X POST http://localhost:[API_PORT]/api/rag-search \
     -H "Content-Type: application/json" \
     -d '{
       "query": "Explain the termination provisions in simple terms",
       "n_results": 5,
       "temperature": 0.7
     }'
   ```

3. **Check system health**:
   ```bash
   curl http://localhost:[API_PORT]/api/health
   ```

## Managing Tenants

### Listing Tenants

```bash
./scripts/deploy_tenant.sh
# Select option 2 from the menu
```

### Stopping a Tenant

```bash
./scripts/deploy_tenant.sh
# Select option 3, then enter the tenant ID
```

### Deleting a Tenant

```bash
./scripts/deploy_tenant.sh
# Select option 4, then enter the tenant ID
```

### Starting a Stopped Tenant

```bash
./scripts/deploy_tenant.sh
# Select option 5, then enter the tenant ID
```

## Troubleshooting

### Common Issues

1. **Port Conflicts**:
   - Ensure each tenant uses unique ports
   - Check for port conflicts with `netstat -tuln`
   - Try stopping other services that might use the same ports

2. **Database Errors**:
   - Verify ChromaDB persistence directory permissions
   - Check for corrupt database files
   - Try reprocessing the documents

3. **API Key Issues**:
   - Ensure each tenant has valid API keys configured
   - Check usage quotas for OpenAI and Google APIs
   - Verify that the keys are correctly set in the environment file

### Logs

Access logs for each tenant:

```bash
# API logs
docker logs legal-search-api-[tenant_id]

# Frontend logs
docker logs legal-search-frontend-[tenant_id]

# Nginx logs
docker logs legal-search-nginx-[tenant_id]
```

### Common Commands

Reset a tenant by stopping, deleting, and recreating:

```bash
# Stop tenant
docker-compose --env-file .env.tenant_name down

# Delete data (if needed)
rm -rf tenants/tenant_name/docs/output/* tenants/tenant_name/docs/chunks/* cache/chroma/tenant_name

# Restart tenant
docker-compose --env-file .env.tenant_name up -d --build
```

## Security Considerations

The current multi-tenant setup provides isolation at the container and data level, but for production environments consider:

1. **Authentication**: Implement proper authentication for tenant access
2. **Network Isolation**: Use separate VLANs or networks for each tenant
3. **API Key Management**: Use a secure method for managing API keys
4. **Data Encryption**: Encrypt sensitive data at rest
5. **Regular Backups**: Implement backup and recovery procedures for tenant data
