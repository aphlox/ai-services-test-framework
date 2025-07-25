#!/bin/bash
set -euo pipefail

# Configuration
MODEL_NAME="phi3"
HEALTH_CHECK_RETRIES=30
HEALTH_CHECK_INTERVAL=2

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

cleanup() {
    log "Shutting down Ollama..."
    kill $OLLAMA_PID 2>/dev/null || true
    wait $OLLAMA_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGTERM SIGINT

# Start Ollama service
log "Starting Ollama service..."
ollama serve &
OLLAMA_PID=$!

# Health check with retries
log "Waiting for Ollama to be ready..."
for i in $(seq 1 $HEALTH_CHECK_RETRIES); do
    if curl -s http://localhost:11434/api/version > /dev/null 2>&1; then
        log "Ollama is ready (attempt $i/$HEALTH_CHECK_RETRIES)"
        break
    fi

    if [ $i -eq $HEALTH_CHECK_RETRIES ]; then
        log "ERROR: Ollama failed to start after $HEALTH_CHECK_RETRIES attempts"
        exit 1
    fi

    log "Waiting for Ollama... (attempt $i/$HEALTH_CHECK_RETRIES)"
    sleep $HEALTH_CHECK_INTERVAL
done

# Pull model with error handling
log "Pulling $MODEL_NAME model..."
if ! ollama pull $MODEL_NAME; then
    log "ERROR: Failed to pull $MODEL_NAME model"
    exit 1
fi

# Verify model is loaded
log "Verifying $MODEL_NAME model..."
if ! ollama list | grep -q $MODEL_NAME; then
    log "ERROR: $MODEL_NAME model not found in loaded models"
    exit 1
fi

log "$MODEL_NAME model is ready. Ollama service running on port 11434"

# Keep container running and handle signals
wait $OLLAMA_PID