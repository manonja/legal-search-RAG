# Legal Document Search RAG System

A Retrieval-Augmented Generation (RAG) system designed for legal document search, combining vector search with LLM capabilities to provide accurate answers to legal queries based on your document corpus.

## Features
- Document processing with multi-format support (PDF, DOC/DOCX)
- Vector search with ChromaDB integration
- Next.js frontend with modern UI
- RAG-powered Q&A for legal documents
- Cost controls for OpenAI API usage
- Multi-tenant support for different user sets
- Cloud storage integration with AWS S3 and Google Cloud

## Development Options

This project can be set up in two ways:

### Option 1: Docker-based (Recommended for Quick Start)
Ideal for quickly testing the application or for production-like environments.

### Option 2: Local Development
Better for active development with hot reloading and direct access to services.

## Option 1: Docker-based Development

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)
- Git

### Setup
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd legal-search-rag
   ```

2. Set environment variables:
   ```bash
   cp api/.env.example api/.env
   # Edit .env to add your OPENAI_API_KEY and GOOGLE_API_KEY (if using Gemini)
   ```

3. Start the containers:
   ```bash
   docker-compose -f shared/docker-compose.yml up -d
   ```

4. Process your documents:
   ```bash
   # Copy your documents
   mkdir -p ~/Downloads/legaldocs
   cp /path/to/your/legal/documents/*.pdf ~/Downloads/legaldocs/

   # Process them
   docker exec legal-search-api-default python process_docs.py
   docker exec legal-search-api-default python chunk.py
   docker exec legal-search-api-default python embeddings.py
   ```

5. Access the application:
   - Frontend: http://localhost:3000
   - API: http://localhost:8000/docs

## Option 2: Local Development

### Prerequisites
- [Pixi](https://pixi.sh) for Python environment management
- Git
- Node.js 18+ (for frontend)

### Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd legal-search-rag
   ```

2. Set up backend:
   ```bash
   cd api
   cp .env.example .env  # Configure your API keys
   pixi install          # Install Python dependencies

   # In a terminal window, start the API server
   pixi run python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000
   ```

3. Set up frontend:
   ```bash
   cd frontend
   npm install

   # In another terminal window, start the frontend
   npm run dev
   ```

4. Process documents:
   ```bash
   cd api

   # Process your documents
   pixi run python process_docs.py
   pixi run python chunk.py
   pixi run python embeddings.py
   ```

5. Access services:
   - Frontend: http://localhost:3000
   - API: http://localhost:8000/docs

## Cloud Deployment (Render.com)

1. Connect your GitHub repository to Render
2. Use the provided `render.yaml` blueprint
3. Set required environment variables:
   - `OPENAI_API_KEY`
   - `GOOGLE_API_KEY` (optional)
   - `GCP_PROJECT_ID` (optional)
   - `GCS_BUCKET_NAME` (optional)

## Usage

### Document Search
Visit http://localhost:3000/search and use keywords like:
- "summary judgment"
- "objection trial"
- "hearsay evidence"

### Legal Q&A
Visit http://localhost:3000/rag-search and ask questions like:
- "How do I file a motion for summary judgment?"
- "What are the rules regarding hearsay evidence?"

## Project Structure
- `api/`: FastAPI backend service
  - Document processing
  - Vector database management
  - RAG search implementation
- `frontend/`: Next.js frontend application
- `shared/`: Configuration and assets
- `scripts/`: Utility scripts

## Technologies
- Backend: Python, FastAPI, LangChain, ChromaDB
- Frontend: Next.js, TypeScript, Tailwind CSS
- AI: OpenAI API and Google Gemini

## License
Apache 2.0
