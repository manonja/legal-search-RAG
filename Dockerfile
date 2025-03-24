# Use a Python base image with conda pre-installed (Mambaforge)
FROM condaforge/mambaforge:latest

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
    tini \
    wget \
    unzip \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Copy configuration files and code
COPY --chown=appuser:appuser . .

# Create cache directory for ChromaDB and query cache
RUN mkdir -p /app/cache/chroma /app/cache/usage && \
    chown -R appuser:appuser /app/cache

# Switch to non-root user
USER appuser
WORKDIR /app

# Install Python dependencies directly with pip instead of relying on pixi
# since pixi.toml only supports osx-64 platform
# Use quotes around version constraints to avoid shell redirection issues
RUN pip install --no-cache-dir \
    PyMuPDF \
    python-docx \
    tqdm \
    google-generativeai \
    Pillow \
    "chromadb>=0.4.22" \
    python-dotenv \
    langchain \
    openai \
    tokenizers \
    fastapi \
    uvicorn \
    pydantic \
    "tiktoken>=0.9.0,<0.10"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:$PORT/api/health || exit 1

# Expose port
EXPOSE $PORT

# Use tini as init
ENTRYPOINT ["/usr/bin/tini", "--"]

# Run the application with uvicorn directly
CMD ["python3", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
