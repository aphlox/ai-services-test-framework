#!/bin/bash
set -euo pipefail

# Configuration
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

# Health check with retries using ollama command
log "Waiting for Ollama to be ready..."
for i in $(seq 1 $HEALTH_CHECK_RETRIES); do
    if ollama list > /dev/null 2>&1; then
        log "Ollama is ready (attempt $i/$HEALTH_CHECK_RETRIES)"
        break
    fi

    if [ $i -eq $HEALTH_CHECK_RETRIES ]; then
        log "WARNING: Ollama may not be fully ready, but continuing..."
        break
    fi

    log "Waiting for Ollama... (attempt $i/$HEALTH_CHECK_RETRIES)"
    sleep $HEALTH_CHECK_INTERVAL
done

log "Ollama service is ready on port 11434"
log "No automatic model download - use 'ollama pull <model>' manually"

# Keep container running and handle signals
wait $OLLAMA_PID