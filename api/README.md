# Legal Search RAG API

The API backend for the Legal Document Search RAG system, built with FastAPI, ChromaDB, and LangChain.

## Features

- **Document Processing**: Extract, chunk, and embed documents
- **Vector Search**: Semantic search using ChromaDB
- **RAG Implementation**: LLM-powered question answering
- **Cost Control**: Token counting and usage monitoring

## Quick Start

### Local Development

1. Install uv (if not already installed):
   ```bash
   curl -sSf https://astral.sh/uv/install.sh | sh
   ```

2. Install dependencies (using pyproject.toml):
   ```bash
   # Install regular dependencies
   make install

   # Install development dependencies
   make install-dev
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env to add your API keys
   ```

4. Process documents:
   ```bash
   make process-docs
   make chunk-docs
   make embed-docs
   ```

5. Start the API server:
   ```bash
   make serve-api
   ```

6. Access the API at http://localhost:8000

### Docker

```bash
# Build the Docker image
docker build -t legal-search-api .

# Run the container with proper volume mounting for data persistence
docker run -p 8000:8000 \
  -v $(pwd)/data/chroma:/data/chroma \
  -v $(pwd)/data/data:/data/data \
  -e OPENAI_API_KEY=your_openai_key \
  -e GOOGLE_API_KEY=your_google_key \
  --env-file .env \
  legal-search-api
```

Environment variables can also be passed via an env file:

```bash
docker run -p 8000:8000 \
  -v $(pwd)/data:/data \
  --env-file .env \
  legal-search-api
```

#### Building and Pushing Docker Images

You can build and push Docker images to different environments using Make:

```bash
# Build and push to development repository
make docker-push ENV=dev

# Build and push to production repository
make docker-push ENV=prod

# Specify a custom version tag (default is 'latest')
make docker-push ENV=prod VERSION=1.0.0
```

Repositories:
- Development: `us-central1-docker.pkg.dev/maja-dev/maja-dev`
- Production: `us-central1-docker.pkg.dev/maja-dev/maja-prod`

For production deployment, consider using Docker Compose:

```yaml
# docker-compose.yml
version: '3'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/data
    env_file:
      - .env
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
```

Start services with:
```bash
docker-compose up -d
```

## API Endpoints

The API provides the following endpoints:

### Health Check
- `GET /api/health`: Extended health check with version information
- `GET /api/health/auth-test`: Test endpoint for authentication (requires token)

### Document Management
- `POST /api/documents/upload`: Upload and process documents (PDF, DOCX)
- `GET /api/documents/{document_id}`: Retrieve document content by ID
- `GET /api/documents/{document_id}/download`: Download the original document file by ID
- `GET /api/documents`: List all available document IDs
- `DELETE /api/documents/{document_id}`: Delete a document and its associated files by ID

### Search & Query
- `POST /api/search`: Perform vector-based semantic search on documents
  - Takes a `SearchQuery` object with `query` and `limit` parameters
  - Example: `{"query": "your search query", "limit": 10}`
- `POST /api/search/api`: Legacy search endpoint with advanced filtering
  - Takes a `QueryRequest` object with additional filtering capabilities
  - Supports metadata filtering (e.g., by document_id)
  - Example: `{"query_text": "your search query", "n_results": 10, "metadata_filter": {"document_id": "your-doc-id"}, "min_similarity": 0.7}`
- `POST /api/query`: RAG-based question answering using documents

### API Documentation
- `GET /api/docs`: Interactive Swagger UI documentation
- `GET /api/redoc`: ReDoc API documentation
- `GET /api/openapi.json`: OpenAPI specification

Visit the documentation at `/api/docs` for complete API details and interactive testing.

## Configuration

Key environment variables:

```bash
# API Keys
OPENAI_API_KEY=your_openai_api_key
GOOGLE_API_KEY=your_google_api_key

# Vector DB Configuration
CHROMA_DB_PATH=/data/chroma
EMBEDDING_MODEL=text-embedding-3-small

# Document Processing
CHUNK_SIZE=512
CHUNK_OVERLAP=50
INPUT_DIR=/data/input
PROCESSED_DIR=/data/processed

# LLM Settings
LLM_MODEL=gpt-4-turbo
MAX_TOKENS=1024
TEMPERATURE=0.0
```

You can customize these variables in your `.env` file. See `.env.example` for a complete list of supported variables.

## Structured Logging

This project uses structlog for JSON-formatted logging:

```python
from struct_logger import log

# Basic usage
log.info("Operation completed")
log.error("Operation failed")

# With structured context
log.info("Document processed", document_id="doc-123", size_kb=1024)

# Log exceptions
try:
    result = process_document()
except Exception as e:
    log.error("Processing failed", error=str(e), exc_info=True)

# Create component-specific logger
db_log = log.bind(component="database")
db_log.info("Query executed", query_time_ms=42)
```

Set `LOG_LEVEL` environment variable to control verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`).

## API Authentication

All API endpoints (except `/api/health` and documentation endpoints) are protected by token-based authentication.

### Token Storage

Authentication tokens are securely stored in Google Cloud Secret Manager. The API is configured to use a secret identified by the full path in Secret Manager:

```
# Full path format used in settings and configuration
API_TOKEN_SECRET_NAME=projects/952577461734/secrets/maja-legal-api-token/versions/1
```

This configuration should be set through environment variables:

```bash
# Authentication settings
GCP_PROJECT_ID=952577461734
API_TOKEN_SECRET_NAME=projects/952577461734/secrets/maja-legal-api-token/versions/1
API_TOKEN=your-api-token  # Optional: Set token directly for local development
```

### Bulk Document Upload

A utility script is provided for batch uploading documents to the API:

```bash
# Make the script executable
chmod +x api/upload_docs.sh

# Usage
./api/upload_docs.sh -u URL -t TOKEN -f FILES

# Example with real values
./api/upload_docs.sh \
  -u "https://maja-legal-api-dev-8aad8c9-y52ot74ira-uc.a.run.app/api/documents/upload" \
  -t "3a57087a8ae7718065992975415fe119e1879f08e9cde4a39379f25f00a9f033" \
  -f "/path/to/documents/*.docx"
```

Parameters:
- `-u, --url`: API endpoint URL
- `-t, --token`: Authorization token
- `-f, --files`: Files to upload (supports wildcards in quotes)
- `-h, --help`: Display help message

### Reading the Token

To view the current token stored in Secret Manager (requires appropriate permissions):

```bash
# Prerequisites: Install Google Cloud SDK and authenticate with gcloud
# gcloud auth login

# Access the specific version as configured in your environment
gcloud secrets versions access 1 --secret="maja-legal-api-token" --project="952577461734"
```

### Using the Token

When making requests to protected endpoints, include the token in the Authorization header:

```bash
# Example: Uploading a document
curl -X POST \
  http://localhost:8000/api/documents/upload \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -F "file=@document.pdf"

# Example: Accessing the auth test endpoint
curl -X GET \
  http://localhost:8000/api/health/auth-test \
  -H "Authorization: Bearer YOUR_API_TOKEN"
```

In Python:
```python
import requests

headers = {"Authorization": f"Bearer {api_token}"}
response = requests.post("http://localhost:8000/api/search",
                         json={"query": "legal precedent"},
                         headers=headers)
```

### Testing

During testing, authentication is automatically disabled. The `TESTING=true` environment variable is set by pytest fixtures to bypass token validation in test environments.

## Testing

This project uses `pytest` for testing. To run the tests:

1.  **Install development dependencies:**

    ```bash
    make install-dev
    ```

2.  **Execute the test suite:**

    ```bash
    uv run pytest
    ```

3.  **Run specific test directories (e.g., integration tests):**

    ```bash
    uv run pytest tests/integration/
    ```

You can use standard `pytest` flags with `uv run`, for example:

```bash
# Run tests verbosely
uv run pytest -v

# Run tests with coverage report for the 'app' directory
uv run pytest --cov=app tests/
```
