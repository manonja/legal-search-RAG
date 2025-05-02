# ---- Builder Stage ----
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

WORKDIR /app

# Install build-time system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Create virtual environment and install dependencies
ENV VENV_PATH=/opt/venv
RUN uv venv $VENV_PATH --python 3.11
# Install dependencies into the virtual environment
RUN uv pip install -r requirements.txt --python $VENV_PATH/bin/python --no-cache

# ---- Final Stage ----
FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04 AS final

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # Set VENV_PATH and add its bin to PATH
    VENV_PATH=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    # For RunPod serverless
    PYTHONPATH=/app \
    # Default model path (can be overridden at runtime)
    MODEL_CACHE_DIR=/cache \
    # Optional HF_EMBEDDING_MODEL env var can be set at runtime
    HF_EMBEDDING_MODEL="nlpaueb/legal-bert-base-uncased"

# Create model cache directory with proper permissions
RUN mkdir -p /cache && chmod 777 /cache

# Install Python and minimal runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-distutils \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create symlink for default python
RUN ln -sf /usr/bin/python3.11 /usr/bin/python

# Set working directory
WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy handler code
COPY handler.py .

# Create a non-root user
RUN useradd -m -u 1000 runpod
RUN chown -R runpod:runpod /app /cache

# Switch to non-root user
USER runpod

# Start the serverless handler
CMD ["python", "handler.py"]
