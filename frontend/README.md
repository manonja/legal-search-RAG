# Legal Search RAG Frontend

The Next.js frontend for the Legal Document Search RAG system, providing a modern interface for document search and AI-powered legal Q&A.

## Features

- **Modern UI**: Built with Next.js, React, and Tailwind CSS
- **Semantic Search**: Find relevant legal document sections
- **RAG-Powered Q&A**: Ask questions about legal documents and get AI-generated answers
- **Responsive Design**: Works on desktop and mobile devices
- **TypeScript**: Type-safe codebase

## Quick Start

### Local Development

1. Install dependencies:
   ```bash
   npm install
   ```

2. Configure environment:
   ```bash
   # Create .env.local file
   echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

4. Access the application at http://localhost:3000

### Production Build

```bash
npm run build
npm run start
```

### Docker Build & Deployment

The project includes a Makefile to simplify Docker image building and deployment to GCP Cloud Run.

#### Prerequisites

- Docker installed locally
- GCP CLI configured for your project
- Access to the specified artifact registries

#### Available Make Commands

```bash
# Show all available commands
make help

# Build for different environments (local is default if ENV not specified)
make build
make ENV=local build
make ENV=dev build
make ENV=prod build

# Push to registry (for dev and prod only)
make ENV=dev push
make ENV=prod push

# Run the local container
make run
# or
make ENV=local run

# Remove local Docker images
make clean
```

#### Version Management

The Docker image versioning is controlled by the `VERSION` file in the project root. Update this file before building production images.

#### Artifact Registry Paths

- Dev: `us-central1-docker.pkg.dev/maja-dev/maja-dev/`
- Prod: `us-central1-docker.pkg.dev/maja-prod/maja-prod/`

## Pages

- `/`: Home page
- `/search`: Document search interface
- `/rag-search`: AI-powered legal Q&A
- `/admin`: Admin dashboard (if enabled)

## Environment Variables

- `NEXT_PUBLIC_API_URL`: URL of the backend API
- `NEXT_PUBLIC_TENANT_ID`: (Optional) Tenant ID for multi-tenant deployments

## Project Structure

- `src/app`: Next.js App Router pages
- `src/components`: Reusable React components
- `src/lib`: Utility functions and API clients
- `public`: Static assets

## License

See the main project repository for license information.
