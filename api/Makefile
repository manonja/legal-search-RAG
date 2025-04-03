.PHONY: install install-dev lint format check-format process-docs chunk-docs embed-docs serve-api lock docker-build docker-push minor patch get-version

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

# Version management
get-version:
	@cat VERSION

# Bump minor version (x.Y.0): increments minor and resets patch to 0
minor:
	@v=$$(cat VERSION | awk -F. '{print $$1"."($$2+1)".0"}'); \
	echo $$v > VERSION; \
	echo "Version updated to $$v"

# Bump patch version (x.y.Z): increments patch
patch:
	@v=$$(cat VERSION | awk -F. '{print $$1"."$$2"."($$3+1)}'); \
	echo $$v > VERSION; \
	echo "Version updated to $$v"

# Docker repository paths
DEV_REPO=us-central1-docker.pkg.dev/maja-dev/maja-dev
PROD_REPO=us-central1-docker.pkg.dev/maja-dev/maja-prod
ENV ?= dev
VERSION = $$(cat VERSION)

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
ifeq ($(ENV),dev)
	$(MAKE) patch
endif
	docker build -t legal-search-api:$(VERSION) --build-arg VERSION_ARG=$(VERSION) .
	docker tag legal-search-api:$(VERSION) $(REPO)/legal-search-api:$(VERSION)

# Push Docker image to repository
docker-push: docker-build
	docker push $(REPO)/legal-search-api:$(VERSION)

# Build Docker image without cache
docker-build-no-cache:
ifeq ($(ENV),dev)
	$(MAKE) patch
endif
	docker build --no-cache -t legal-search-api:$(VERSION) --build-arg VERSION_ARG=$(VERSION) .
	docker tag legal-search-api:$(VERSION) $(REPO)/legal-search-api:$(VERSION)
