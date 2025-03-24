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
    && rm -rf /var/lib/apt/lists/*

# Install pixi
RUN curl -fsSL https://pixi.sh/install.sh | bash && \
    echo 'export PATH="$HOME/.pixi/bin:$PATH"' >> ~/.bashrc

# Make sure pixi is in the PATH
ENV PATH="/root/.pixi/bin:$PATH"

# Copy pixi configuration files
COPY pixi.toml pixi.lock ./

# Initialize environment with pixi
RUN pixi install

# Create cache directory for ChromaDB and query cache
RUN mkdir -p /app/cache/chroma /app/cache/usage

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/api/health || exit 1

# Expose port
EXPOSE $PORT

# Start the application with Gunicorn through pixi
CMD ["/bin/bash", "-c", "source ~/.pixi/env && pixi run serve-api"]
