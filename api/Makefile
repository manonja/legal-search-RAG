.PHONY: install install-dev lint format check-format process-docs chunk-docs embed-docs serve-api lock check-deps

# Install dependencies using uv
install: lock
	echo "Installing from uv.lock and pyproject.toml..."
	uv pip sync pyproject.toml -v
	uv pip install -e .
	@echo "Checking for missing dependencies..."
	@make check-deps

# Install development dependencies
install-dev: install
	uv pip install -e ".[dev]"

# Lock dependencies
lock:
	./scripts/lock-dependencies.sh

# Check if dependencies are properly installed
check-deps:
	@echo "Verifying that chromadb is installed..."
	@python -c "import chromadb; print(f'chromadb version: {chromadb.__version__}')" || echo "chromadb is not installed properly!"
	@echo "Verifying that other key packages are installed..."
	@python -c "import langchain, openai, tiktoken, fastapi, uvicorn, pydantic, sentence_transformers; print('All key packages are installed')" || echo "Some packages are missing!"

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
