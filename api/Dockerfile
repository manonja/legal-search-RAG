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
    # ChromaDB specific settings
    CHROMA_DIR=/data/chroma \
    DATA_DIR=/data/data \
    COLLECTION_NAME=legal_docs \
    LOG_LEVEL=INFO \
    # UV settings
    UV_SYSTEM_PYTHON=1 \
    SENTRY_DSN=https://sentry.io/api/1234567890/store/ \
    PORT=8000

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

# Switch to non-root user
USER appuser

# Expose port
EXPOSE ${PORT}

# Volume for persistent data (essential for ChromaDB)
VOLUME ["/data/chroma", "/data/data"]

# Run the application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", ${PORT}, "--workers", "1"]
