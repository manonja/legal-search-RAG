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
- **Multi-Tenant Support**: Deploy isolated instances for different users or document sets
- **Cloud Storage Integration**: Support for both AWS S3 and Google Cloud Storage
- **OpenAI API Cost Controls**:
  - Token counting and cost estimation
  - Per-query, daily, and monthly cost thresholds
  - Quota management system for limiting usage
  - Usage tracking and reporting dashboard
  - Cost warnings for expensive requests

## Screenshots
![Search Interface](assets/images/search-interface.png)
![RAG Results](assets/images/rag-results.png)

## Quick Start

### Option 1: Single-User Development Setup

#### Prerequisites
- [Pixi](https://pixi.sh) - A fast, modern package manager built on top of Conda
- Git
- Node.js 18+ (for Next.js frontend)

#### Setup
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
   # Edit .env to add your OPENAI_API_KEY and GOOGLE_API_KEY
   ```

4. Add your legal documents (PDF/DOCX) to the input directory:
   ```bash
   mkdir -p ~/Downloads/legaldocs
   cp /path/to/your/legal/documents/*.pdf ~/Downloads/legaldocs/
   ```

5. Process documents (extract, chunk, and embed):
   ```bash
   pixi run process-docs    # Convert documents to text
   pixi run chunk-docs      # Split into chunks
   pixi run embed-docs      # Generate embeddings
   ```

6. Start the API server:
   ```bash
   pixi run serve-api
   ```

7. In a new terminal, start the Next.js frontend:
   ```bash
   cd nextjs-legal-search
   npm install
   npm run dev
   ```

8. Open your browser to http://localhost:3000

### Option 2: Multi-Tenant Deployment with Docker

For deployments with multiple users or isolated document sets:

#### Quick Start (Recommended for New Users)
1. Make sure Docker and Docker Compose are installed
2. Run our interactive quick start script:
   ```bash
   ./scripts/quick_start.sh
   ```
3. Follow the prompts to create a new tenant, add documents, and process them
4. Access your system at the URL provided at the end of the script

#### Manual Deployment
1. Run the tenant deployment script:
   ```bash
   ./scripts/deploy_tenant.sh
   ```
2. Follow the interactive prompts to create a new tenant
3. Add documents to the tenant's input directory using our helper script:
   ```bash
   ./scripts/add_documents.sh tenant_name
   ```
   Or manually:
   ```bash
   cp /path/to/your/documents/*.pdf tenants/tenant_name/docs/input/
   ```
4. Process the documents:
   ```bash
   ./scripts/process_tenant_docs.sh tenant_name
   ```
5. Access the tenant's interface at the URL provided after deployment

For full details, see our [Multi-Tenant Deployment Guide](MULTI_TENANT_DEPLOYMENT.md).

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
- **AI**: OpenAI API and Google Gemini for embeddings and completions
- **Cloud Storage**: AWS S3 and Google Cloud Storage integration

## Project Status
Active development - core features implemented, optimizations ongoing

## License
Apache 2.0

## Performance Metrics
- 83% accuracy in legal QA benchmarks
- Sub-2 second latency for query processing
- Comprehensive testing protocol covering various legal query types

## Project Structure

- `api.py` - FastAPI backend with RAG search endpoints
- `utils/` - Utility modules:
  - `token_counter.py` - Token counting and cost estimation utilities
  - `usage_db.py` - SQLite database for tracking usage and quota
- `middleware/` - FastAPI middleware:
  - `cost_control.py` - Middleware for enforcing cost controls
- `api/` - API modules:
  - `admin.py` - Admin endpoints for monitoring usage

## Environment Variables

Create a `.env` file with the following variables:

```
OPENAI_API_KEY=your_openai_api_key
ADMIN_API_KEY=your_admin_key_for_dashboard
USAGE_DB_PATH=usage.db
```

## Running the Application

### Backend
```bash
uvicorn api:app --reload
```

### Frontend
```bash
cd nextjs-legal-search
npm run dev
```

## Cost Control Features

### Token Counting and Cost Estimation

The system includes utilities to count tokens and estimate costs before making API calls:

```python
from utils.token_counter import estimate_tokens_and_cost

# Estimate cost before making API call
cost_estimate = estimate_tokens_and_cost(messages, model, max_tokens)
```

### Usage Tracking

All API calls are logged to a SQLite database with token usage and cost information:

```python
from utils.usage_db import log_api_usage

# Log API usage after completion
log_api_usage(
    conversation_id=conversation_id,
    query_text=query,
    model=model,
    input_tokens=input_tokens,
    output_tokens=output_tokens,
    total_tokens=total_tokens,
    cost=actual_cost
)
```

### Cost Thresholds

The system enforces cost thresholds at different levels:

- **Per-query threshold**: Warns or blocks expensive individual queries
- **Daily threshold**: Limits total daily spending
- **Monthly threshold**: Ensures you stay within a monthly budget

### Monthly Query Quota

Implement a quota system to limit the number of queries per month:

```python
from utils.usage_db import check_quota_exceeded

# Check if quota is exceeded
if check_quota_exceeded():
    raise HTTPException(status_code=429, detail="Monthly quota exceeded")
```

### Admin Dashboard

Access the admin dashboard at `/admin` to:

- View current usage statistics
- Monitor costs and token usage
- Update quota and threshold settings
- Project monthly costs based on current usage

## Deployment

The system can be deployed in several ways:

### Local Deployment
For testing and development, you can run the application locally:

```bash
# Start the FastAPI backend
pixi run serve-api

# Start the Next.js frontend
cd nextjs-legal-search
npm run dev
```

### Docker Deployment
For containerized deployment:

```bash
# Build and start all services
docker-compose up -d
```

### Cloud Deployment

#### Render.com Deployment
We provide a comprehensive guide for deploying to Render.com:
- [Render.com Deployment Guide](docs/render_deployment.md)

#### AWS and Google Cloud Storage Integration
The system supports both AWS S3 and Google Cloud Storage for document storage:

1. Set up GCP storage:
   ```bash
   ./scripts/setup_local_gcp.sh /path/to/gcp-credentials.json
   ```

2. Upload documents to GCP:
   ```bash
   python scripts/upload_to_gcs.py /path/to/document.pdf
   ```

For more details on cloud deployment, see the [Cloud Deployment Guide](docs/cloud_deployment.md).

#### Key Cloud Deployment Features
- **S3 Document Storage**: Persistent storage for documents
- **Container-based Deployment**: Consistent environments
- **Automated Deployment Scripts**: Streamline the deployment process
- **Cost-efficient**: Minimal resource requirements (~$15-25/month)
- **Easy Sharing**: Simple to share with clients or team members
