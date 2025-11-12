# CodeGenie Dockerfile
# Multi-stage build for optimized image size

# Stage 1: Base image with Python and dependencies
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Stage 2: Install Ollama
FROM base as ollama

# Install Ollama
RUN curl -fsSL https://ollama.ai/install.sh | sh

# Stage 3: Application
FROM ollama as app

# Create app directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
COPY setup.py .
COPY pyproject.toml .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/

# Install CodeGenie
RUN pip install -e .

# Create necessary directories
RUN mkdir -p /root/.config/codegenie \
    /root/.cache/codegenie \
    /root/.codegenie/logs \
    /root/.codegenie/sessions

# Copy default configuration
COPY config/default_config.yaml /root/.config/codegenie/config.yaml

# Expose ports
EXPOSE 8000 11434

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:11434/api/tags || exit 1

# Create startup script
COPY scripts/docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["codegenie", "--host", "0.0.0.0", "--port", "8000"]
