#!/bin/bash

# Enhanced Download Script with Resumable Logic
MODEL_NAME="llama3.2:3b"
MAX_ATTEMPTS=50
ATTEMPT=1
PROGRESS_FILE="/tmp/ollama_download_progress.txt"
DOWNLOAD_PID_FILE="/tmp/ollama_download.pid"
CHECKPOINT_INTERVAL=60  # Check progress every 60 seconds

# Network optimization
export OLLAMA_DOWNLOAD_TIMEOUT=1800  # 30 minutes per attempt
export OLLAMA_RETRY_DELAY=5
export OLLAMA_MAX_RETRIES=3

# Logging functions
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a /home/rhox/lama_test/enhanced_download.log
}

cleanup() {
    if [ -f "$DOWNLOAD_PID_FILE" ]; then
        local pid=$(cat "$DOWNLOAD_PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            log "Cleaning up process $pid"
            kill -TERM "$pid" 2>/dev/null
            sleep 5
            kill -KILL "$pid" 2>/dev/null
        fi
        rm -f "$DOWNLOAD_PID_FILE"
    fi
}

trap cleanup EXIT

# Check current progress
get_download_progress() {
    local progress_output=$(docker exec ollama-phi4 ollama list 2>/dev/null | grep "$MODEL_NAME" || echo "")
    if [ -n "$progress_output" ]; then
        echo "100"  # Model is complete
    else
        # Try to get partial download info from storage
        local storage_size=$(docker exec ollama-phi4 du -sb /root/.ollama 2>/dev/null | cut -f1 || echo "0")
        # Estimate progress based on storage (rough approximation)
        local progress=$((storage_size * 100 / 2147483648))  # 2GB target
        echo "$progress"
    fi
}

# Monitor download progress
monitor_progress() {
    local download_pid=$1
    local last_progress=0
    local stall_counter=0
    local max_stall_time=300  # 5 minutes of no progress = stall
    
    while kill -0 "$download_pid" 2>/dev/null; do
        sleep "$CHECKPOINT_INTERVAL"
        
        local current_progress=$(get_download_progress)
        echo "$current_progress" > "$PROGRESS_FILE"
        
        if [ "$current_progress" -eq "$last_progress" ]; then
            stall_counter=$((stall_counter + CHECKPOINT_INTERVAL))
            log "Progress stalled at $current_progress% for ${stall_counter}s"
            
            if [ "$stall_counter" -ge "$max_stall_time" ]; then
                log "Download stalled for ${max_stall_time}s, terminating"
                kill -TERM "$download_pid"
                return 1
            fi
        else
            log "Progress: $current_progress% (was $last_progress%)"
            last_progress=$current_progress
            stall_counter=0
        fi
        
        # Check if complete
        if [ "$current_progress" -eq 100 ]; then
            log "Download completed successfully!"
            return 0
        fi
    done
    
    return 1
}

# Enhanced download function
perform_download() {
    log "Starting download attempt $ATTEMPT of $MAX_ATTEMPTS"
    
    # Start download in background
    {
        docker exec ollama-phi4 sh -c "
            export OLLAMA_DOWNLOAD_TIMEOUT=$OLLAMA_DOWNLOAD_TIMEOUT
            export OLLAMA_RETRY_DELAY=$OLLAMA_RETRY_DELAY
            export OLLAMA_MAX_RETRIES=$OLLAMA_MAX_RETRIES
            ollama pull '$MODEL_NAME'
        "
    } &
    
    local download_pid=$!
    echo "$download_pid" > "$DOWNLOAD_PID_FILE"
    log "Download started with PID $download_pid"
    
    # Monitor progress
    if monitor_progress "$download_pid"; then
        return 0
    else
        log "Download monitoring failed, checking final status"
        wait "$download_pid"
        return $?
    fi
}

# Main execution
log "Starting enhanced download for $MODEL_NAME"
log "System: $(free -h | grep Mem:)"
log "Container: $(docker stats ollama-phi4 --no-stream)"

# Initialize progress file
echo "0" > "$PROGRESS_FILE"

while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
    log "=== Attempt $ATTEMPT/$MAX_ATTEMPTS ==="
    
    # Check if model already exists
    if docker exec ollama-phi4 ollama list | grep -q "$MODEL_NAME"; then
        log "✅ Model $MODEL_NAME already downloaded!"
        exit 0
    fi
    
    # Perform download with monitoring
    if perform_download; then
        log "✅ Model $MODEL_NAME downloaded successfully on attempt $ATTEMPT!"
        exit 0
    fi
    
    log "❌ Attempt $ATTEMPT failed, waiting before retry..."
    
    # Exponential backoff with jitter
    local wait_time=$((10 + (ATTEMPT * 5) + (RANDOM % 10)))
    log "Waiting ${wait_time} seconds before next attempt..."
    sleep "$wait_time"
    
    ATTEMPT=$((ATTEMPT + 1))
done

log "❌ Failed to download model after $MAX_ATTEMPTS attempts"
exit 1