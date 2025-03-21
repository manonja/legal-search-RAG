# Use Python 3.9 slim image as base
FROM python:3.9-slim

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
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Gunicorn
RUN pip install --no-cache-dir gunicorn

# Create cache directory for ChromaDB and query cache
RUN mkdir -p /app/cache/chroma /app/cache/usage

# Create non-root user and switch to it
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Copy application code
COPY --chown=appuser:appuser . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/api/health || exit 1

# Expose port
EXPOSE $PORT

# Start the application with Gunicorn
CMD gunicorn api:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT --timeout 120
