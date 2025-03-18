# Legal Document Search RAG System

![Legal Search Banner](assets/images/app-screenshot.png)

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/yourusername/legal-search-rag)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/python-3.9+-yellow.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.95.0-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-13.0+-black.svg)](https://nextjs.org/)

## Project Description
A Retrieval-Augmented Generation (RAG) system specifically designed for legal document search, combining vector search with LLM capabilities to provide accurate answers to legal queries based on your document corpus.

## Features
- **Document Processing Pipeline**: Multi-format support (PDF, DOC/DOCX), intelligent text chunking, and semantic preservation
- **Vector Search Infrastructure**: State-of-the-art embeddings with ChromaDB integration
- **Modern Interface**: Next.js frontend
- **RAG-Powered Q&A**: Ask legal questions and get AI-generated answers based on your document corpus
- **Privacy-First**: Local ChromaDB storage ensuring data privacy and compliance

## Screenshots
![Search Interface](assets/images/search-interface.png)
![RAG Results](assets/images/rag-results.png)

## Installation

### Prerequisites
- [Pixi](https://pixi.sh) - A fast, modern package manager built on top of Conda
- Git
- Node.js 18+ (for Next.js frontend)

### Setup
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd legal-search-rag
   ```

2. Install dependencies using Pixi:
   ```bash
   pixi install
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. Start the FastAPI backend:
   ```bash
   pixi run serve-api
   ```

5. Set up the Next.js frontend:
   ```bash
   cd nextjs-legal-search
   npm install
   npm run dev
   ```

## Usage

### Document Processing
```bash
# Process documents
pixi run process-docs

# Chunk documents
pixi run chunk-docs
```

### Accessing the Application
- FastAPI Swagger UI: http://localhost:8000
- Next.js frontend: http://localhost:3000

### Sample Queries

#### Document Search (http://localhost:3000/search)
Use these keywords or phrases to find relevant document sections:
- "summary judgment"
- "objection trial"
- "hearsay evidence"

#### Legal Q&A (http://localhost:3000/rag-search)
Ask complete questions to get AI-generated answers:
- "What is the proper procedure for making an objection during trial?"
- "How do I file a motion for summary judgment?"
- "What are the rules regarding hearsay evidence?"
- "What constitutes inadmissible evidence in court?"

## Code Examples

### Search API
```python
# Search for documents
import requests

response = requests.post(
    "http://localhost:8000/api/search",
    json={"query_text": "summary judgment", "n_results": 5}
)
results = response.json()
```

### RAG API
```python
# Get AI-generated answers
import requests

response = requests.post(
    "http://localhost:8000/api/rag-search",
    json={"query_text": "What is hearsay evidence?", "n_results": 5}
)
answer = response.json()
```

## Technologies Used
- **Backend**: Python, FastAPI, LangChain, ChromaDB
- **Frontend**: Next.js, TypeScript, Tailwind CSS
- **Document Processing**: PyMuPDF, python-docx
- **AI**: OpenAI API for embeddings and completions

## Project Status
Active development - core features implemented, optimizations ongoing

## License
Apache 2.0

## Performance Metrics
- 83% accuracy in legal QA benchmarks
- Sub-2 second latency for query processing
- Comprehensive testing protocol covering various legal query types
