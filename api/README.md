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
docker build -t legal-search-api .
docker run -p 8000:8000 -v $(pwd)/cache:/app/cache legal-search-api
```

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
