# Use a Python base image
FROM python:3.10-slim

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

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir \
    PyMuPDF \
    python-docx \
    tqdm \
    Pillow \
    "chromadb>=0.4.18" \
    python-dotenv \
    langchain \
    openai \
    tokenizers \
    fastapi \
    uvicorn \
    pydantic \
    "tiktoken>=0.9.0,<0.10" \
    "grpcio>=1.54.0" \
    "protobuf>=4.22.3" \
    grpcio-tools \
    && pip install --upgrade pip

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
CMD ["python", "-m", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
