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
   # Create .env.local file from example
   cp .env.example .env.local
   # Edit .env.local with your configuration
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

## Docker Build & Deployment

The project includes a Makefile to simplify Docker image building and deployment to GCP Cloud Run.

### Prerequisites

- Docker installed locally
- GCP CLI configured for your project
- Access to the specified artifact registries

### Environment Variables

The following environment variables can be passed to the Docker container:

- `NEXT_PUBLIC_API_URL`: URL of the backend API (required)
- `SENTRY_DSN`: Sentry DSN for error tracking
- `ADMIN_PASSWORD`: Password for admin access
- `USER_PASSWORD`: Password for user access
- `API_TOKEN`: Token for API authentication

### Building and Pushing Docker Images

You can build and push Docker images to different environments using Make:

```bash
# Show all available commands
make help

# Build for local environment
make ENV=local build

# Build and push to development repository (automatically bumps patch version)
make ENV=dev docker-push

# Build and push to production repository
make ENV=prod docker-push

# Manually bump version numbers
make minor  # Increments minor version (x.Y.0)
make patch  # Increments patch version (x.y.Z)
make get-version  # Display current version
```

### Running the Docker Container Locally

```bash
# Run with environment variables
make ENV=local run NEXT_PUBLIC_API_URL=http://localhost:8000 SENTRY_DSN=your_sentry_dsn ADMIN_PASSWORD=admin_password USER_PASSWORD=user_password API_TOKEN=your_api_token

# Alternatively, you can run the Docker container directly:
docker run -p 3000:10000 \
  -e NEXT_PUBLIC_API_URL=http://localhost:8000 \
  -e SENTRY_DSN=your_sentry_dsn \
  -e ADMIN_PASSWORD=admin_password \
  -e USER_PASSWORD=user_password \
  -e API_TOKEN=your_api_token \
  legal-search-frontend:0.1.0
```

The Docker container runs on port 10000 internally but is mapped to port 3000 on your local machine for development. This means you should access the application at http://localhost:3000 in your browser.

For dummy values during development, you can use:
```bash
make ENV=local build NEXT_PUBLIC_API_URL=http://localhost:8000 ADMIN_PASSWORD=dummy USER_PASSWORD=dummy API_TOKEN=dummy SENTRY_DSN=dummy
make ENV=local run NEXT_PUBLIC_API_URL=http://localhost:8000 ADMIN_PASSWORD=dummy USER_PASSWORD=dummy API_TOKEN=dummy SENTRY_DSN=dummy
```

### Repositories and Environments

- **Local**: Builds the image locally without pushing to any registry
- **Development**: Pushes to `us-central1-docker.pkg.dev/maja-dev/maja-dev/legal-search-frontend:[VERSION]`
- **Production**: Pushes to `us-central1-docker.pkg.dev/maja-dev/maja-prod/legal-search-frontend:[VERSION]`

### Version Management

The Docker image versioning is controlled by the `VERSION` file in the project root.
- In development builds, the patch version is automatically incremented
- For production builds, you should manually set the version using `make minor` or `make patch`

## Pages

- `/`: Home page
- `/search`: Document search interface
- `/rag-search`: AI-powered legal Q&A
- `/admin`: Admin dashboard (if enabled)

## Project Structure

- `src/app`: Next.js App Router pages
- `src/components`: Reusable React components
- `src/lib`: Utility functions and API clients
- `public`: Static assets

## License

See the main project repository for license information.
