#!/bin/bash

# CodeGenie Docker Entrypoint Script

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Starting CodeGenie...${NC}"

# Start Ollama service in background
echo -e "${GREEN}Starting Ollama service...${NC}"
ollama serve > /var/log/ollama.log 2>&1 &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo -e "${GREEN}Waiting for Ollama to be ready...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e "${GREEN}Ollama is ready!${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${YELLOW}Warning: Ollama may not be ready${NC}"
    fi
    sleep 1
done

# Check if models need to be pulled
if [ -n "$OLLAMA_MODELS" ]; then
    echo -e "${GREEN}Pulling Ollama models: $OLLAMA_MODELS${NC}"
    IFS=',' read -ra MODELS <<< "$OLLAMA_MODELS"
    for model in "${MODELS[@]}"; do
        echo -e "${GREEN}Pulling model: $model${NC}"
        ollama pull "$model" || echo -e "${YELLOW}Warning: Failed to pull $model${NC}"
    done
fi

# Run database migrations if needed
if [ -f "/app/alembic.ini" ]; then
    echo -e "${GREEN}Running database migrations...${NC}"
    alembic upgrade head || echo -e "${YELLOW}Warning: Migration failed${NC}"
fi

# Initialize CodeGenie if needed
if [ ! -f "/root/.codegenie/initialized" ]; then
    echo -e "${GREEN}Initializing CodeGenie...${NC}"
    codegenie init --non-interactive || true
    touch /root/.codegenie/initialized
fi

# Handle shutdown gracefully
cleanup() {
    echo -e "${GREEN}Shutting down...${NC}"
    kill $OLLAMA_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGTERM SIGINT

# Execute the main command
echo -e "${GREEN}Starting CodeGenie application...${NC}"
exec "$@"
