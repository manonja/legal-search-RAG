# Legal Search RAG API

The API backend for the Legal Document Search RAG system, built with FastAPI, ChromaDB, and LangChain.

## Features

- **Document Processing**: Extract, chunk, and embed documents
- **Vector Search**: Semantic search using ChromaDB
- **RAG Implementation**: LLM-powered question answering
- **Cost Control**: Token counting and usage monitoring
- **Cloud Storage**: AWS S3 and GCP integration

## Quick Start

### Local Development

1. Install dependencies:
   ```bash
   pixi install
   # or
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env to add your API keys
   ```

3. Process documents:
   ```bash
   python process_docs.py
   python chunk.py
   python embeddings.py
   ```

4. Start the API server:
   ```bash
   python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000
   ```

5. Access the API at http://localhost:8000

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
- `USE_GCP_STORAGE`: Set to 'true' to use GCP
- `GCP_PROJECT_ID`: Your GCP project ID
- `GCS_BUCKET_NAME`: Your GCS bucket name
- `DOCUMENTS_DIR`: Path to documents directory
- `LIMIT_TOKENS_PER_MINUTE`: Token rate limit
- `LIMIT_TOKENS_PER_DAY`: Daily token limit

## Project Structure

- `api.py`: Main FastAPI application
- `process_docs.py`: Document processing
- `chunk.py`: Text chunking
- `embeddings.py`: Generate embeddings
- `query.py`: Search implementation
- `api_modules/`: API endpoint modules
- `middleware/`: FastAPI middleware
- `utils/`: Utility functions
