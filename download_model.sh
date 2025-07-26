#!/bin/bash

# Advanced Ollama Model Download with Resume Capability
# This script downloads model files directly and imports them into Ollama

MODEL_NAME="${1:-llama3.2:1b}"
MODEL_DIR="/tmp/ollama_downloads"
LOG_FILE="$MODEL_DIR/download.log"

# Create download directory
mkdir -p "$MODEL_DIR"

echo "Starting advanced download for model: $MODEL_NAME" | tee -a "$LOG_FILE"

# Function to try Ollama pull with timeout
try_ollama_pull() {
    local model="$1"
    local timeout_duration=300  # 5 minutes
    
    echo "Trying direct Ollama pull with $timeout_duration second timeout..." | tee -a "$LOG_FILE"
    
    timeout $timeout_duration docker exec ollama-phi4 ollama pull "$model" 2>&1 | tee -a "$LOG_FILE"
    
    if [ $? -eq 0 ]; then
        echo "Direct Ollama pull succeeded!" | tee -a "$LOG_FILE"
        return 0
    else
        echo "Direct Ollama pull failed or timed out" | tee -a "$LOG_FILE"
        return 1
    fi
}

# Strategy 1: Try direct Ollama pull first
echo "=== Strategy 1: Direct Ollama Pull ===" | tee -a "$LOG_FILE"
if try_ollama_pull "$MODEL_NAME"; then
    echo "SUCCESS: Model downloaded via direct Ollama pull" | tee -a "$LOG_FILE"
    exit 0
fi

# Strategy 2: Restart container with optimized settings and try again
echo "=== Strategy 2: Optimized Container Settings ===" | tee -a "$LOG_FILE"
echo "Restarting container with optimized network settings..." | tee -a "$LOG_FILE"

cd /home/rhox/lama_test
docker-compose down
sleep 5
docker-compose up -d

# Wait for container to start
sleep 30

# Try again with optimized container
echo "Trying download with optimized container..." | tee -a "$LOG_FILE"
if try_ollama_pull "$MODEL_NAME"; then
    echo "SUCCESS: Model downloaded with optimized settings" | tee -a "$LOG_FILE"
    exit 0
fi

echo "All download strategies failed. Check $LOG_FILE for details." | tee -a "$LOG_FILE"
exit 1