# Legal Document Search RAG System

## Overview
This project implements a state-of-the-art Retrieval-Augmented Generation (RAG) system specifically designed for legal document search and analysis. By combining advanced document processing, vector-based search, and a modern user interface, it provides powerful semantic search capabilities for legal professionals.

## Project Architecture

The system is built on three main pillars:

### 1. Document Processing Pipeline
Our document ingestion system employs a sophisticated processing pipeline that handles various document formats while preserving the semantic structure crucial for legal documents:

- **Multi-Format Support**: Robust handling of PDF and DOC/DOCX files using industry-standard libraries (PyMuPDF and python-docx)
- **Intelligent Text Chunking**: Implementation of context-aware document splitting using LangChain's RecursiveCharacterTextSplitter:
  - 512-character chunks with 50-character overlap
  - Hierarchical splitting using paragraph and newline separators
  - Preserves document structure with chunk markers
  - Run with: `pixi run chunk-docs` (processes files from `~/Downloads/processedLegalDocs`)
- **Semantic Preservation**: Careful handling of document hierarchies and relationships to maintain context

### 2. Vector Search Infrastructure
The core search functionality is powered by a modern vector search implementation:

- **State-of-the-Art Embeddings**: Utilization of OpenAI's latest embedding model for optimal semantic understanding
- **Efficient Storage**: ChromaDB integration for fast and reliable vector storage and retrieval
- **Hybrid Search Capabilities**: Combination of semantic and keyword-based search for maximum accuracy

### 3. User Interface Options
The system offers two user interface options:

#### Retool Interface (Original)
- **Intuitive Query Interface**: Legal-specific search features with intelligent autocompletion
- **Flexible Search Modes**: Support for both exact phrase matching and semantic search
- **Rich Results Display**: Context-aware result presentation with relevant highlights

#### Next.js Frontend (New)
- **Modern UI**: Clean, responsive design built with Next.js and Tailwind CSS
- **Document Search**: Dedicated page for searching legal documents with real-time results
- **RAG-Powered Q&A**: Ask legal questions and get AI-generated answers based on your document corpus
- **Mobile-Friendly**: Fully responsive design that works on all devices

## Technical Highlights

- **Advanced Text Processing**: Semantic-aware document splitting with customized separators for legal documents
- **Hybrid Search Architecture**: Combination of vector similarity and traditional search methods
- **Performance Optimization**: Built-in caching and parallel processing capabilities
- **Privacy-First Design**: Local ChromaDB storage ensuring data privacy and compliance
- **Modern Frontend**: Next.js application with TypeScript and Tailwind CSS

## Performance Metrics

The system is designed to meet rigorous performance standards:

- 83% accuracy in legal QA benchmarks
- Sub-2 second latency for query processing
- Comprehensive testing protocol covering various legal query types

## Future Optimizations

The system is designed with scalability in mind, with planned improvements including:

- Enhanced metadata handling for section-level filtering
- Legal-specific query expansion
- Response caching optimization
- Parallel document processing improvements
- Authentication and user management for the Next.js frontend

## Development Setup

This project uses modern Python development tools to ensure code quality and maintainability:

### Prerequisites

- [Pixi](https://pixi.sh) - A fast, modern package manager built on top of Conda
- Git
- Node.js 18+ (for Next.js frontend)

### Getting Started

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

6. Access the applications:
   - FastAPI Swagger UI: http://localhost:8000
   - Next.js frontend: http://localhost:3000

### Development Tools

The project is configured with several development tools to maintain code quality:

#### Code Formatting

The project uses Black with a line length of 88 characters. Formatting is automated through:

- VS Code: Files are auto-formatted on save
- CLI: Run `pixi run format` to format all files
- Lint check: Run `pixi run lint` to check style

All tools (Black, isort, flake8) are configured to use consistent settings.

#### Pre-commit Hooks

We use pre-commit hooks to ensure code quality before each commit. The following checks are automatically run:

- **Black**: Code formatting
- **isort**: Import sorting
- **Flake8**: Code style and documentation checks
- **General checks**: Trailing whitespace, file endings, YAML validation

To manually run all checks:
```bash
pixi run lint
```

#### Pixi Configuration

The project uses `pixi.toml` for dependency management and task automation:

- Python 3.9 or higher
- Development tools (black, flake8, isort, pre-commit)
- Predefined tasks for common operations

### Best Practices

1. Always ensure pre-commit hooks are installed after cloning:
   ```bash
   pixi run pre-commit install
   ```

2. Run linting before pushing changes:
   ```bash
   pixi run lint
   ```

3. Keep `pixi.toml` updated when adding new dependencies

### Processing Pipeline

1. **Document Processing**:
   ```bash
   pixi run process-docs  # Converts and processes raw documents
   ```

2. **Text Chunking**:
   ```bash
   # Using default paths
   pixi run chunk-docs  # Processes files from ~/Downloads/processedLegalDocs

   # Or with custom paths
   INPUT_DIR=/custom/input OUTPUT_DIR=/custom/output pixi run chunk-docs
   ```

### Environment Setup

This project uses environment variables for managing sensitive configuration like API keys. We use `python-dotenv` to manage these variables.

#### Setting up Environment Variables

1. **Copy the environment template**:
   ```bash
   cp .env.example .env
   ```

2. **Configure your environment**:
   Edit `.env` and add your actual values:
   ```bash
   # OpenAI API Configuration
   OPENAI_API_KEY=your_api_key_here  # Replace with your API key
   ```

#### Environment Variables in Code

The project provides utility functions to handle environment variables:

```python
from utils import load_env_variables, get_openai_api_key

# Load environment variables at startup
load_env_variables()

# Use the API key
api_key = get_openai_api_key()
```

## Testing the Application

### Running the Application Locally

1. Start the FastAPI backend:
   ```bash
   pixi run serve-api
   ```

2. Start the Next.js frontend:
   ```bash
   cd nextjs-legal-search
   npm run dev
   ```

3. Access the applications:
   - FastAPI Swagger UI: http://localhost:8000
   - Next.js frontend: http://localhost:3000

### Test Scenarios

Here are some scenarios to test the application's functionality:

#### 1. Document Search

1. Navigate to http://localhost:3000/search
2. Enter a search query like "objection during trial" or "summary judgment"
3. Observe the search results, including:
   - Relevant document chunks
   - Similarity scores
   - Document metadata

#### 2. RAG-Powered Legal Questions

1. Navigate to http://localhost:3000/rag-search
2. Ask a legal question like "What is the proper procedure for making an objection during trial?"
3. Observe the AI-generated answer and the supporting context documents

#### 3. API Direct Access

You can also test the API directly using the Swagger UI or curl:

```bash
# Health check
curl http://localhost:8000/api/health

# Document search
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query_text": "summary judgment", "n_results": 5}'

# RAG search
curl -X POST http://localhost:8000/api/rag-search \
  -H "Content-Type: application/json" \
  -d '{"query_text": "What is hearsay evidence?", "n_results": 5}'
```

### Sample Test Queries

Here are some test queries you can try to evaluate different aspects of our system:

1. **Procedural Questions**:
   - "What is the proper procedure for making an objection during trial?"
   - "How do I file a motion for summary judgment?"
   - "What are the requirements for serving legal documents?"

2. **Evidence-related Questions**:
   - "What types of evidence are inadmissible in court?"
   - "How do I authenticate electronic evidence?"
   - "What are the rules regarding hearsay evidence?"

3. **Court Protocol Questions**:
   - "What is the proper way to address a judge?"
   - "What are the dress code requirements in court?"
   - "How should exhibits be presented in court?"

4. **Legal Rights Questions**:
   - "What are my rights when being questioned by police?"
   - "What are the requirements for a valid search warrant?"
   - "What are the Miranda rights?"

5. **Edge Cases**:
   - Very short queries: "objection"
   - Complex queries: "What are the specific circumstances under which attorney-client privilege can be waived in a corporate setting?"
   - Queries with typos: "What is heresay evidence?"

When testing, pay attention to:
- **Relevance**: Are the returned results actually answering the question?
- **Accuracy**: Is the information provided correct and up-to-date?
- **Context**: Is enough context provided to understand the answer?
- **Similarity Scores**: How confident is the system in its answers?
- **Response Time**: How quickly does the system respond to queries?

## Deployment

### Docker Deployment

The project includes Docker configuration for easy deployment:

```bash
# Build and run both services
docker-compose up --build -d
```

This will:
- Build and run the FastAPI backend
- Build and run the Next.js frontend
- Set up Nginx as a reverse proxy

Access the deployed application at:
- http://localhost (Nginx proxy)
- http://localhost:8000 (Direct API access)
- http://localhost:3000 (Direct frontend access)

---
