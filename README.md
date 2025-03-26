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

This project can be set up in three ways:

### Option 1: Docker-based (Recommended for Quick Start)
Ideal for quickly testing the application or for production-like environments.

### Option 2: Local Development
Better for active development with hot reloading and direct access to services.

### Option 3: Render.com Deployment
For production deployment using Render.com.

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

2. Run the setup script:
   ```bash
   ./scripts/run_with_docker.sh
   ```

3. Process your documents:
   ```bash
   ./scripts/process_docs_docker.sh
   ```

4. Access the application:
   - Frontend: http://localhost:3000
   - API: http://localhost:8001/docs

For more details, see [DOCKER_SETUP.md](DOCKER_SETUP.md).

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

## Deployment to Render.com

This project includes a `render.yaml` Blueprint for easy deployment:

1. Push your code to a Git repository
2. Connect your GitHub repository to Render
3. Deploy as a Blueprint using the provided `render.yaml` file
4. Set required environment variables:
   - `OPENAI_API_KEY`
   - `GOOGLE_API_KEY` (optional)

After deployment, your services will be available at:
- Frontend: https://legal-search-frontend.onrender.com
- API: https://legal-search-api.onrender.com

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
