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
  -v $(pwd)/data:/data \
  -v $(pwd)/data/chroma:/data/chroma \
  -v $(pwd)/data/input:/data/input \
  -v $(pwd)/data/processed:/data/processed \
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

### Document Management
- `POST /api/documents/upload`: Upload and process documents (PDF, DOCX)
- `GET /api/documents/{document_id}`: Retrieve document content by ID

### Search & Query
- `POST /api/search`: Perform vector-based semantic search on documents
- `POST /api/search/api`: Legacy search endpoint (backward compatibility)
- `POST /api/query`: RAG-based question answering using documents

### API Documentation
- `GET /api/docs`: Interactive Swagger UI documentation
- `GET /api/redoc`: ReDoc API documentation
- `GET /api/openapi.json`: OpenAPI specification

Visit the documentation at `/api/docs` for complete API details and interactive testing.

## Configuration

Key environment variables:

```bash
# ... existing code ...
