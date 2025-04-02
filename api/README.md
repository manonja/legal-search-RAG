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

## Running with Docker

To run the container properly with environment variables:

```bash
# Run the container with environment variables
docker run -p 8000:8000 \
  -v $(pwd)/data:/data \
  -v $(pwd)/data/chroma:/data/chroma \
  -v $(pwd)/data/input:/data/input \
  -v $(pwd)/data/processed:/data/processed \
  --env-file .env \
  -e SENTRY_DSN=https://your-sentry-dsn \
  legal-search-api
```

Remember to:
1. Never bake secrets into the container
2. Pass all necessary environment variables at runtime
3. Use Docker secrets for production environments
4. Keep different .env files for different environments (dev, staging, prod)
5. Consider using a vault service for sensitive credentials in production

## API Endpoints

- `GET /api/health`: Health check endpoint
- `POST /api/search`: Perform semantic search
- `POST /api/rag-search`: Ask questions and get AI-generated answers
- `GET /api/usage`: Get API usage statistics
- `POST /api/upload`: Upload documents

## Configuration

Key environment variables:

- `OPENAI_API_KEY`: Your OpenAI API key
- `GOOGLE_API_KEY`: Your Google API key (optional, for Gemini)
- `DOCUMENTS_DIR`: Path to documents directory
- `LIMIT_TOKENS_PER_MINUTE`: Token rate limit
- `LIMIT_TOKENS_PER_DAY`: Daily token limit

## Project Structure

```
app/
├── api/                  # API endpoints
│   └── endpoints/        # API endpoint modules
├── core/                 # Core application code
│   └── config.py         # Configuration settings
├── db/                   # Database utilities
├── models/               # Data models
├── schemas/              # Pydantic schemas
├── services/             # Business logic services
│   ├── chunk.py          # Text chunking
│   ├── embeddings.py     # Generate embeddings
│   ├── process_docs.py   # Document processing
│   └── query.py          # Search implementation
├── utils/                # Utility functions
│   ├── env.py            # Environment utilities
│   └── usage_db.py       # Usage tracking
└── main.py               # Main FastAPI application
```

## Development

- **Linting**: `make lint`
- **Formatting**: `make format`
- **Check Formatting**: `make check-format`

## Dependency Management

This project uses:
- **pyproject.toml**: For defining all project dependencies and metadata (PEP 621 standard)
- **uv**: Fast Python package installer and resolver
- **Python 3.11**: Required for compatibility with all dependencies

To lock dependencies for consistent installations:
```bash
make lock
```
