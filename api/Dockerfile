# Use a Python base image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PORT=8000

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Create cache directory for ChromaDB and query cache
RUN mkdir -p /app/cache/chroma /app/cache/usage && \
    chown -R appuser:appuser /app/cache

# Install uv
RUN curl -sSf https://astral.sh/uv/install.sh | sh && \
    mv -f ~/.cargo/bin/uv /usr/local/bin/uv

# Copy project files
COPY --chown=appuser:appuser pyproject.toml ./

# Install dependencies with uv
RUN uv pip install -e .

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

# Expose port
EXPOSE $PORT

# Run the application
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
