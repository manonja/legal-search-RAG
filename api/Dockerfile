FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

# Set working directory
WORKDIR /app

# Copy all necessary files for installation
COPY pyproject.toml README.md ./

# Set UV to use system Python
ENV UV_SYSTEM_PYTHON=1

# Install dependencies from pyproject.toml
RUN uv pip install --no-cache -e .

# Second stage
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PORT=8000 \
    # ChromaDB specific settings
    CHROMA_DATA_DIR=/data/chroma \
    DATA_ROOT=/data \
    INPUT_DIR=/data/input \
    OUTPUT_DIR=/data/processed \
    DOCS_ROOT=/data/docs \
    CHUNKS_DIR=/data/chunks \
    COLLECTION_NAME=legal_docs \
    # Tenant settings
    TENANT_ROOT=/data/tenants/default \
    CACHE_DIR=/data/tenants/default/cache \
    # API settings
    API_HOST=0.0.0.0 \
    API_PORT=8000 \
    HOST=0.0.0.0 \
    LOG_LEVEL=INFO \
    # UV settings
    UV_SYSTEM_PYTHON=1 \
    SENTRY_DSN=https://sentry.io/api/1234567890/store/

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser

# Create required directories and set permissions
RUN mkdir -p /data/chroma /data/input /data/processed /data/docs /data/chunks /data/tenants/default/cache && \
    chown -R appuser:appuser /data && \
    chown -R appuser:appuser /app

# Copy installed dependencies from builder stage
COPY --from=builder --chown=appuser:appuser /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Copy application code (excluding .env files)
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Expose port
EXPOSE ${PORT}

# Volume for persistent data (essential for ChromaDB)
VOLUME ["/data/chroma", "/data/input", "/data/processed", "/data/docs", "/data/chunks", "/data/tenants"]

# Run the application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
