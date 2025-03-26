# Docker Setup for Legal Search RAG

This document explains how to use Docker for local development and deployment to Render.com.

## Local Development with Docker

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Setup and Run

1. **Run the setup script**:

   ```bash
   ./scripts/run_with_docker.sh
   ```

   This script will:
   - Check for Docker and Docker Compose installation
   - Set up your `.env` file if it doesn't exist
   - Create the necessary data directories from environment variables
   - Set up the frontend `.env.local` file
   - Start the Docker containers using the shared/docker-compose.yml file

2. **Process documents**:

   ```bash
   ./scripts/process_docs_docker.sh
   ```

   This script will:
   - Check if the Docker container is running
   - Prompt you to add documents if none exist in the input directory
   - Process, chunk, and embed the documents

3. **Access the application**:
   - Frontend: http://localhost:3000
   - API: http://localhost:8001/docs

### Docker Compose Commands

- **View logs**:
  ```bash
  docker compose -f shared/docker-compose.yml logs -f
  ```

- **Stop containers**:
  ```bash
  docker compose -f shared/docker-compose.yml down
  ```

- **Rebuild and restart**:
  ```bash
  docker compose -f shared/docker-compose.yml up --build -d
  ```

## Deployment to Render.com

This project is configured for easy deployment to Render.com using a Blueprint.

### Steps to Deploy

1. Push your code to a Git repository (GitHub, GitLab, etc.)

2. Connect your repository to Render.com

3. Deploy as a Blueprint using the `render.yaml` file

   This will automatically:
   - Deploy the API service with a persistent disk
   - Deploy the frontend service
   - Connect them together

### Important Configuration Notes

- **API Service**: Runs on port 8000 inside the container
- **Frontend Service**: Connects to the API service URL automatically
- **Persistent Storage**: A 10GB disk is mounted at `/app/data` for document storage

## Project Structure

- `api/`: FastAPI backend service with Dockerfile
- `frontend/`: Next.js frontend application with Dockerfile
- `shared/`: Contains docker-compose.yml for local development
- `scripts/`: Utility scripts for Docker setup and operation
- `render.yaml`: Blueprint definition for Render.com deployment
