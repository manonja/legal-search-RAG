# Local Development Setup

This guide will help you set up and run the Legal Search RAG system in local development mode.

## Prerequisites

- [Pixi](https://pixi.sh) for Python environment management
- [Node.js](https://nodejs.org/) (v18+) for the frontend
- PDF and DOCX documents to process (optional)

## Step 1: Install Dependencies

```bash
# Install Python dependencies
pixi install

# Install frontend dependencies
cd frontend && npm install
```

## Step 2: Configure Environment

```bash
# Copy example environment files
cp api/.env.example api/.env

# Edit API keys in api/.env if needed
# - Update GOOGLE_API_KEY with your Google API key
# - Update OPENAI_API_KEY with your OpenAI API key
```

## Step 3: Set Up Directory Structure

```bash
# Run the directory setup script
./scripts/setup_dirs.sh
```

This script will:
- Create the directory structure defined in your `.env` file
- Set up backward compatibility with legacy paths
- Ensure all required directories exist

By default, data will be stored in `~/legal-search-data/` with the following subdirectories:
- `input`: Raw documents (PDF, DOCX)
- `processed`: Extracted text
- `chunks`: Chunked documents
- `chroma`: Vector database

## Step 4: Process Documents (Optional)

Place your legal documents (PDF, DOCX) in the input directory (default: `~/legal-search-data/input` or the symlinked `~/Downloads/legaldocs_input`).

```bash
# Run the document processing pipeline
pixi run process-docs  # Extract text from documents
pixi run chunk-docs    # Split documents into chunks
pixi run embed-docs    # Generate embeddings for search
```

## Step 5: Run the Backend and Frontend

In one terminal, start the API server:

```bash
pixi run serve-api
# or use the script:
./scripts/run_local.sh
```

In another terminal, start the frontend:

```bash
cd frontend && npm run dev
# or use the script:
./scripts/run_frontend.sh
```

## Access the Application

- Frontend: http://localhost:3000
- API docs: http://localhost:8000/docs

## Helper Scripts

We've provided several helper scripts to make development easier:

- `scripts/setup_dirs.sh`: Creates the necessary directory structure
- `scripts/run_local.sh`: Runs the API server with document processing
- `scripts/run_frontend.sh`: Runs the frontend server

## Troubleshooting

- **Missing dependencies**: Run `pixi install` to ensure all dependencies are installed
- **Port conflicts**: Edit the `API_PORT` in `api/.env` if port 8000 is in use
- **Document processing issues**: Ensure your PDFs are text-based, not scanned images
- **Directory issues**: Run `./scripts/setup_dirs.sh` to recreate the directory structure
