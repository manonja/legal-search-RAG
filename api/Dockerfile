FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

# Set working directory
WORKDIR /app

# Copy all necessary files for installation
COPY pyproject.toml README.md VERSION uv.lock ./

# Set UV to use system Python
ENV UV_SYSTEM_PYTHON=1

# Install dependencies using frozen lockfile
RUN uv sync --frozen

# Second stage
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim

# Set working directory
WORKDIR /app

# Add version label from VERSION file
COPY --from=builder /app/VERSION /app/VERSION
ARG VERSION_ARG
RUN if [ -z "$VERSION_ARG" ]; then \
    export VERSION_ARG=$(cat /app/VERSION); \
    fi && \
    echo "Building image version: $VERSION_ARG"

LABEL version="$VERSION_ARG" \
    description="Legal Document RAG API" \
    maintainer="maja"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    # ChromaDB specific settings
    CHROMA_DIR=/data/chroma \
    DATA_DIR=/data/data \
    COLLECTION_NAME=legal_docs \
    LOG_LEVEL=INFO \
    # UV settings
    UV_SYSTEM_PYTHON=1 \
    SENTRY_DSN=https://sentry.io/api/1234567890/store/ \
    PORT=8000 \
    API_TOKEN=your_api_token_here

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser

# Create required directories and set permissions
RUN mkdir -p /data/chroma /data/data && \
    chown -R appuser:appuser /data && \
    chown -R appuser:appuser /app

# Copy installed dependencies from builder stage
COPY --from=builder --chown=appuser:appuser /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Copy application code (excluding .env files)
COPY --chown=appuser:appuser . .

# Create a startup script
RUN echo '#!/bin/sh\n\
    exec python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1\n\
    ' > /app/docker-entrypoint.sh && \
    chmod +x /app/docker-entrypoint.sh

# Switch to non-root user
USER appuser

# Expose port
EXPOSE ${PORT}

# Volume for persistent data (essential for ChromaDB)
VOLUME ["/data/chroma", "/data/data"]

# Run the application
CMD ["/app/docker-entrypoint.sh"]
