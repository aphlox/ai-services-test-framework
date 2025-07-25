# Technical Specifications & Requirements

## System Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Audio Input   │    │     Whisper     │    │     Ollama      │
│   (.wav, .mp3)  │───▶│  Transcription  │───▶│   LLM + Phi-4   │
│                 │    │    Service      │    │     Mini        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Test Suite    │    │   Unit Tests    │    │ Integration     │
│   Framework     │    │   (pytest)     │    │    Tests        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Hardware Requirements & Resource Allocation

### System Specifications
- **Total System Memory:** 17GB available
- **CPU:** Multi-core processor (4+ cores recommended)
- **Storage:** 50GB+ free space
- **Network:** Reliable internet for model downloads
- **GPU:** Optional (CUDA-compatible for acceleration)

### Memory Allocation Strategy
```
Total Memory: 17GB
├── System Reserve: 2GB (12%)
├── Docker Engine: 1GB (6%)
├── Ollama Container: 8GB (47%)
├── Whisper Service: 4GB (24%)
└── Testing/Buffer: 2GB (11%)
```

### Container Resource Limits
```yaml
# Ollama Container Limits
deploy:
  resources:
    limits:
      memory: 8G
      cpus: '4'
    reservations:
      memory: 4G
      cpus: '2'
```

## Docker Configuration Specifications

### Docker Compose Complete Configuration
```yaml
version: '3.8'

services:
  ollama:
    image: ollama/ollama:latest
    container_name: ollama-phi4
    ports:
      - "11434:11434"
    volumes:
      - ollama-data:/root/.ollama
      - ./entrypoint.sh:/entrypoint.sh:ro
      - ./models:/models:ro
    environment:
      - OLLAMA_KEEP_ALIVE=5m
      - OLLAMA_HOST=0.0.0.0
      - OLLAMA_ORIGINS=*
      - OLLAMA_NUM_PARALLEL=2
      - OLLAMA_MAX_LOADED_MODELS=1
    entrypoint: ["/entrypoint.sh"]
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 8G
          cpus: '4'
        reservations:
          memory: 4G
          cpus: '2'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/version"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  whisper-api:
    build:
      context: .
      dockerfile: Dockerfile.whisper
    container_name: whisper-service
    ports:
      - "8000:8000"
    volumes:
      - ./audio_data:/app/audio_data:ro
      - ./models/whisper:/app/models:rw
    environment:
      - WHISPER_MODEL=base
      - WHISPER_DEVICE=cpu
      - COMPUTE_TYPE=int8
    deploy:
      resources:
        limits:
          memory: 4G
          cpus: '2'
        reservations:
          memory: 2G
          cpus: '1'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  ollama-data:
    driver: local
  whisper-models:
    driver: local

networks:
  ai-services:
    driver: bridge
```

### Advanced Entrypoint Script
```bash
#!/bin/bash
set -euo pipefail

# Configuration
MODEL_NAME="phi4"
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
```

### Dockerfile for Whisper Service
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY tests/ ./tests/

# Create directories
RUN mkdir -p /app/audio_data /app/models

# Expose port
EXPOSE 8000

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["python", "-m", "uvicorn", "src.whisper_api:app", "--host", "0.0.0.0", "--port", "8000"]
```

## API Specifications & Endpoints

### Whisper Service API
```python
# FastAPI endpoint specifications
from fastapi import FastAPI, UploadFile, HTTPException
from pydantic import BaseModel
from typing import Optional, List

class TranscriptionResponse(BaseModel):
    text: str
    language: str
    language_probability: float
    duration: float
    word_count: int
    processing_time: float

class TranscriptionRequest(BaseModel):
    model_size: Optional[str] = "base"
    language: Optional[str] = None
    temperature: Optional[float] = 0.0
    beam_size: Optional[int] = 5

# Endpoints
@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio(
    audio: UploadFile,
    request: TranscriptionRequest = TranscriptionRequest()
):
    """Transcribe uploaded audio file"""
    pass

@app.get("/models")
async def list_available_models():
    """List available Whisper models"""
    return ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"]

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow()}
```

### Ollama Service API Extensions
```python
class StructuredRequest(BaseModel):
    prompt: str
    schema: Dict[str, Any]
    model: Optional[str] = "phi4"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2048

class FunctionCallRequest(BaseModel):
    prompt: str
    tools: List[Dict[str, Any]]
    model: Optional[str] = "phi4"
    temperature: Optional[float] = 0.7

class PerformanceMetrics(BaseModel):
    response_time: float
    tokens_per_second: float
    memory_usage: float
    model_load_time: float

# Custom endpoints for enhanced functionality
@app.post("/structured-generate")
async def generate_structured_response(request: StructuredRequest):
    """Generate structured JSON response"""
    pass

@app.post("/function-call")
async def execute_function_call(request: FunctionCallRequest):
    """Execute function calling"""
    pass

@app.get("/metrics")
async def get_performance_metrics() -> PerformanceMetrics:
    """Get current performance metrics"""
    pass
```

## Model Specifications & Performance Characteristics

### Phi-4-Mini Model Details
```yaml
Model Specifications:
  Name: phi4
  Architecture: Transformer-based LLM
  Parameters: 3.8B
  Context Length: 4096 tokens
  Quantization Options:
    - Q4_K_M: 4-bit quantization (recommended)
    - Q8_0: 8-bit quantization (higher quality)
    - FP16: Half precision (best quality, more memory)

Performance Characteristics:
  Memory Requirements:
    - Q4_K_M: ~2.5GB VRAM/RAM
    - Q8_0: ~4.2GB VRAM/RAM
    - FP16: ~7.6GB VRAM/RAM

  Speed Benchmarks:
    - Tokens/Second: 20-50 t/s (CPU)
    - Response Time: 2-5 seconds (typical)
    - Cold Start: 10-15 seconds
    - Warm Inference: <1 second initialization
```

### Faster-Whisper Model Details
```yaml
Model Specifications:
  Available Sizes:
    - tiny: 39 MB, ~32x realtime speed
    - base: 74 MB, ~16x realtime speed
    - small: 244 MB, ~6x realtime speed
    - medium: 769 MB, ~2x realtime speed
    - large-v2: 1550 MB, ~1x realtime speed
    - large-v3: 1550 MB, ~1x realtime speed

  Recommended Configuration:
    Model: base
    Device: cpu
    Compute Type: int8
    Beam Size: 5

  Performance Characteristics:
    Memory Usage:
      - tiny: ~1GB RAM
      - base: ~1.5GB RAM
      - small: ~2GB RAM
      - medium: ~3GB RAM
      - large: ~4GB RAM

    Processing Speed:
      - 1 minute audio: ~15-30 seconds processing
      - Word Error Rate: 5-15% (depending on audio quality)
      - Languages: 99+ supported languages
```

## Testing Framework Architecture

### Test Configuration Matrix
```yaml
Test Categories:
  Unit Tests:
    - Whisper transcription accuracy
    - Ollama structured output validation
    - Schema validation
    - Error handling
    - Mock integrations

  Integration Tests:
    - End-to-end pipeline
    - Container connectivity
    - API response validation
    - Service health checks

  Performance Tests:
    - Response time benchmarks
    - Memory usage monitoring
    - Concurrent request handling
    - Load testing scenarios

  Edge Case Tests:
    - Invalid inputs
    - Network failures
    - Timeout scenarios
    - Resource exhaustion
```

### Testing Data Requirements
```yaml
Audio Test Data:
  Formats: [wav, mp3, flac, ogg]
  Sample Rates: [8000, 16000, 22050, 44100, 48000]
  Durations: [1s, 10s, 60s, 300s, 1800s]
  Quality Levels: [clean, noisy, compressed]
  Languages: [en, es, fr, de, zh, ja]

Text Test Data:
  Prompt Categories:
    - Simple queries
    - Complex multi-step instructions
    - Function calling scenarios
    - Edge cases and adversarial inputs
    - Multilingual prompts

  Schema Validation:
    - Simple object schemas
    - Nested object structures
    - Array validations
    - Optional/required field combinations
    - Type validation scenarios
```

### Coverage Requirements
```yaml
Code Coverage Targets:
  Unit Tests: ≥90%
  Integration Tests: ≥80%
  Overall Coverage: ≥85%

Performance Benchmarks:
  Whisper Transcription:
    - Processing Time: <2x audio duration
    - Memory Usage: <4GB peak
    - Word Error Rate: <15%

  Ollama LLM:
    - Response Time: <10 seconds
    - Memory Usage: <8GB peak
    - Token Throughput: >15 t/s

  End-to-End Pipeline:
    - Total Processing: <45 seconds
    - Success Rate: >95%
    - Error Recovery: <5 seconds
```

## Security & Compliance Specifications

### Security Considerations
```yaml
Data Security:
  - No audio data persistence beyond processing
  - Secure temporary file handling
  - Memory cleanup after processing
  - Container isolation

API Security:
  - Rate limiting implementation
  - Input validation and sanitization
  - Error message sanitization
  - Request size limits

Container Security:
  - Non-root user execution
  - Read-only file systems where possible
  - Minimal base images
  - Regular security updates
```

### Monitoring & Observability
```yaml
Metrics Collection:
  - Response times and latencies
  - Error rates and types
  - Resource utilization (CPU, memory)
  - Model performance metrics

Logging Strategy:
  - Structured JSON logging
  - Request/response correlation IDs
  - Performance timing logs
  - Error and exception tracking

Health Checks:
  - Service availability checks
  - Model loading verification
  - Resource threshold monitoring
  - Dependency health validation
```

## Deployment & Scaling Specifications

### Environment Configuration
```yaml
Development:
  - Single container deployment
  - Local model storage
  - Debug logging enabled
  - Hot reload for development

Production:
  - Multi-container orchestration
  - External model storage
  - Optimized logging
  - Health check automation

Scaling Considerations:
  - Horizontal pod autoscaling
  - Load balancer configuration
  - Shared model storage
  - Connection pooling
```

### Backup & Recovery
```yaml
Backup Strategy:
  - Model files backup
  - Configuration backup
  - Container image versioning
  - Data retention policies

Recovery Procedures:
  - Automated failover
  - Health check recovery
  - Model reloading procedures
  - Service restart automation
```

---

**Document Version:** 1.0
**Last Updated:** [Current Date]
**Maintained By:** AI Services Development Team
