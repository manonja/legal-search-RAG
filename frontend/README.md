# Legal Search RAG Frontend

A Next.js frontend for the Legal Search RAG application, deployed on Google Cloud Run.

## Development

### Prerequisites

- Node.js 18 or later
- npm 9 or later

### Setup

1. Install dependencies:

```bash
npm install
```

2. Create a `.env.local` file with the following variables:

```
NEXT_PUBLIC_API_URL=http://localhost:8080
```

3. Start the development server:

```bash
npm run dev
```

The app will be available at [http://localhost:3000](http://localhost:3000).

## Building and deploying

### Local build

To build the app locally:

```bash
npm run build
```

### Using Makefile (Recommended)

The project includes a Makefile to simplify Docker image building and deployment:

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

### Manual Docker build

Alternatively, you can build the Docker image manually:

```bash
docker build -t legal-search-frontend:latest .
```

### Testing the Docker image locally

```bash
# Using make
make ENV=local run NEXT_PUBLIC_API_URL=http://localhost:8080

# Or directly with Docker
docker run -p 3000:3000 -e NEXT_PUBLIC_API_URL=http://localhost:8080 legal-search-frontend:latest
```

### Deploying to Cloud Run

The frontend is automatically deployed to Google Cloud Run using Pulumi. The deployment process is as follows:

1. Update the version in `infra/VERSION-frontend_cloud_run-dev` (for development) or `infra/VERSION-frontend_cloud_run-prod` (for production)

2. Build and push the Docker image using the Makefile:
   ```bash
   make ENV=dev docker-push  # For development
   make ENV=prod docker-push  # For production
   ```

   Or manually:
   ```bash
   # Authenticate with Google Cloud
   gcloud auth configure-docker us-central1-docker.pkg.dev

   # Tag the image with the correct repository
   docker tag legal-search-frontend:latest us-central1-docker.pkg.dev/[PROJECT_ID]/[REPOSITORY]/legal-search-frontend:latest

   # Push the image
   docker push us-central1-docker.pkg.dev/[PROJECT_ID]/[REPOSITORY]/legal-search-frontend:latest
   ```

3. Deploy using Pulumi:
   ```bash
   cd infra
   pulumi up
   ```

## Health Checks

The app includes a health check endpoint at `/api/health` which returns a 200 OK response with a JSON payload `{ "status": "ok" }`. This endpoint is used by Cloud Run to determine if the app is healthy.

## Environment Variables

- `NEXT_PUBLIC_API_URL`: URL of the backend API
- `NEXT_PUBLIC_ENVIRONMENT`: Environment name (dev, staging, prod)

## Project Structure

```
frontend/
├── app/                  # Next.js App Router
│   ├── api/              # API routes
│   │   └── health/       # Health check endpoint
│   │   └── search/       # Search routes
│   │   └── admin/        # Admin routes
│   ├── components/       # Reusable components
│   ├── layout.js         # Root layout
│   └── page.js           # Home page
├── public/               # Static assets
├── Dockerfile            # Docker configuration
├── next.config.js        # Next.js configuration
└── package.json          # Dependencies and scripts
```

## Features

- **Modern UI**: Built with Next.js, React, and Tailwind CSS
- **Semantic Search**: Find relevant legal document sections
- **RAG-Powered Q&A**: Ask questions about legal documents and get AI-generated answers
- **Responsive Design**: Works on desktop and mobile devices
- **TypeScript**: Type-safe codebase

## Pages

- `/`: Home page
- `/search`: Document search interface
- `/rag-search`: AI-powered legal Q&A
- `/admin`: Admin dashboard (if enabled)

## License

See the main project repository for license information.
