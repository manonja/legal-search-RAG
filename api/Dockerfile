# ---- Builder Stage ----
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

WORKDIR /app

# Install build-time system dependencies (if any are needed by uv or package builds)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy project files needed for build
COPY pyproject.toml README.md VERSION ./

# Create virtual environment and install dependencies
ENV VENV_PATH=/opt/venv
RUN uv venv $VENV_PATH --python 3.11
# Install dependencies into the virtual environment
RUN uv pip install . --python $VENV_PATH/bin/python --no-cache

# ---- Final Stage ----
FROM python:3.11-slim-bookworm AS final

# Set environment variables needed for runtime
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # Set VENV_PATH and add its bin to PATH
    VENV_PATH=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    # Runtime specific settings
    CHROMA_DIR=/data/chroma \
    DATA_DIR=/data/data \
    COLLECTION_NAME=legal_docs \
    LOG_LEVEL=INFO \
    SENTRY_DSN=https://sentry.io/api/1234567890/store/ \
    PORT=8000 \
    # Consider secrets management for production
    API_TOKEN=your_api_token_here

# Create non-root user
RUN useradd -m -u 1000 appuser

# Create required directories and set permissions
RUN mkdir -p /data/chroma /data/data && \
    chown -R appuser:appuser /data

# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder --chown=appuser:appuser /opt/venv /opt/venv

# Copy application code (Ensure your app code is in an 'app' directory)
COPY --chown=appuser:appuser app /app/app
# Copy the VERSION file needed at runtime
COPY --from=builder --chown=appuser:appuser /app/VERSION /app/VERSION

# Create a startup script that uses python from the venv (implicitly via PATH)
RUN echo '#!/bin/sh\n\
    echo "Running uvicorn with python: $(which python)"\n\
    python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1\n\
    ' > /app/docker-entrypoint.sh && \
    chmod +x /app/docker-entrypoint.sh && \
    chown appuser:appuser /app/docker-entrypoint.sh

# Switch to non-root user
USER appuser

# Expose port
EXPOSE ${PORT}

# Volume for persistent data
VOLUME ["/data/chroma", "/data/data"]

# Run the application using the entrypoint script
CMD ["/app/docker-entrypoint.sh"]
