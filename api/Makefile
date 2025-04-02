.PHONY: install install-dev lint format check-format process-docs chunk-docs embed-docs serve-api lock docker-build docker-push

# Install dependencies using uv
install:
	uv pip install -e .

# Install development dependencies
install-dev:
	uv pip install -e ".[dev]"

# Lock dependencies
lock:
	./scripts/lock-dependencies.sh

# Lint the codebase
lint:
	ruff check . --exclude=.pixi

# Format the codebase
format:
	ruff format . --exclude=.pixi

# Check formatting
check-format:
	ruff format . --check --exclude=.pixi

# Process documents
process-docs:
	python -m app.services.process_docs

# Chunk documents
chunk-docs:
	python -m app.services.chunk

# Embed documents
embed-docs:
	python -m app.services.embeddings

# Start the API server
serve-api:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Docker repository paths
DEV_REPO=us-central1-docker.pkg.dev/maja-dev/maja-dev
PROD_REPO=us-central1-docker.pkg.dev/maja-dev/maja-prod
ENV ?= dev
VERSION ?= latest

# Set repository based on environment
ifeq ($(ENV),dev)
	REPO=$(DEV_REPO)
else ifeq ($(ENV),prod)
	REPO=$(PROD_REPO)
else
	$(error ENV must be 'dev' or 'prod')
endif

# Build Docker image
docker-build:
	docker build -t legal-search-api:$(VERSION) .
	docker tag legal-search-api:$(VERSION) $(REPO)/legal-search-api:$(VERSION)

# Push Docker image to repository
docker-push: docker-build
	docker push $(REPO)/legal-search-api:$(VERSION)
