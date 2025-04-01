.PHONY: install install-dev lint format check-format process-docs chunk-docs embed-docs serve-api lock

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
