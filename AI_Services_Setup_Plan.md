# AI Services Setup & Testing Implementation Plan

## Executive Summary

This document outlines the complete implementation plan for setting up a robust AI services environment with Docker containerization, Whisper speech-to-text transcription, Ollama LLM with Phi-4-Mini model, and comprehensive unit testing framework. The plan is designed for a WSL2 Linux environment with 17GB available memory.

## System Requirements & Prerequisites

### Hardware Requirements
- **Memory**: 17GB RAM available (current system)
- **Storage**: 50GB+ free space for Docker images and models
- **CPU**: Multi-core processor (4+ cores recommended)
- **GPU**: Optional but recommended for faster processing

### Software Prerequisites
- WSL2 Linux environment (current setup)
- Python 3.9+
- Internet connection for downloading models and Docker images

## Phase 1: Environment Setup (2-3 hours)

### 1.1 Docker Installation

#### Method: Official Docker Repository (Recommended)
```bash
# Remove conflicting packages
for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do
    sudo apt-get remove $pkg;
done

# Update and install prerequisites
sudo apt-get update
sudo apt-get install ca-certificates curl

# Add Docker's official GPG key and repository
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Post-installation configuration
sudo groupadd docker
sudo usermod -aG docker $USER
sudo systemctl enable docker.service
sudo systemctl enable containerd.service
```

#### Verification
```bash
# Test Docker installation
docker run hello-world
docker --version
docker compose version
```

### 1.2 Whisper Fast Installation

#### Method: faster-whisper (4x faster than original)
```bash
# Create virtual environment
python3 -m venv whisper-env
source whisper-env/bin/activate

# Install faster-whisper with GPU support
pip install faster-whisper

# For CUDA 12 + cuDNN 9 support
pip install nvidia-cublas-cu12 nvidia-cudnn-cu12==9.*

# Install additional dependencies
pip install pytest pydantic numpy scipy librosa
```

#### Verification
```python
from faster_whisper import WhisperModel

# Test installation
model = WhisperModel("base", device="cpu", compute_type="int8")
segments, info = model.transcribe("test_audio.wav")
print(f"Detected language: {info.language}")
```

### 1.3 Ollama Container with Phi-4-Mini

#### Docker Compose Configuration
Create `docker-compose.yml`:
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
      - ./entrypoint.sh:/entrypoint.sh
    environment:
      - OLLAMA_KEEP_ALIVE=5m
      - OLLAMA_HOST=0.0.0.0
    entrypoint: ["/entrypoint.sh"]
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 8G
        reservations:
          memory: 4G

volumes:
  ollama-data:
```

#### Entrypoint Script
Create `entrypoint.sh`:
```bash
#!/bin/bash
set -e

# Start Ollama in background
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "Waiting for Ollama to start..."
while ! curl -s http://localhost:11434/api/version > /dev/null; do
    sleep 2
done

echo "Ollama started, pulling Phi-4-Mini model..."
ollama pull phi4

echo "Phi-4-Mini model ready. Ollama is running on port 11434"

# Keep container running
wait $OLLAMA_PID
```

#### Deployment
```bash
# Make entrypoint executable
chmod +x entrypoint.sh

# Deploy container
docker compose up -d

# Verify deployment
curl http://localhost:11434/api/tags
```

## Phase 2: Testing Framework Implementation (2-3 hours)

### 2.1 Project Structure
```
ai-services-testing/
├── tests/
│   ├── test_whisper.py
│   ├── test_ollama.py
│   ├── test_integration.py
│   └── conftest.py
├── src/
│   ├── whisper_service.py
│   ├── ollama_service.py
│   └── schemas.py
├── test_data/
│   ├── audio/
│   └── prompts/
├── requirements.txt
└── pytest.ini
```

### 2.2 Audio Transcription Tests

#### Service Implementation (`src/whisper_service.py`)
```python
from faster_whisper import WhisperModel
from typing import Dict, Any
import logging

class WhisperService:
    def __init__(self, model_size: str = "base", device: str = "cpu"):
        self.model = WhisperModel(model_size, device=device, compute_type="int8")
        self.logger = logging.getLogger(__name__)

    def transcribe(self, audio_path: str) -> Dict[str, Any]:
        try:
            segments, info = self.model.transcribe(audio_path, beam_size=5)

            transcript = ""
            word_count = 0

            for segment in segments:
                transcript += segment.text + " "
                word_count += len(segment.text.split())

            return {
                "text": transcript.strip(),
                "language": info.language,
                "language_probability": info.language_probability,
                "duration": info.duration,
                "word_count": word_count
            }
        except Exception as e:
            self.logger.error(f"Transcription failed: {e}")
            raise
```

#### Test Implementation (`tests/test_whisper.py`)
```python
import pytest
import tempfile
import numpy as np
import scipy.io.wavfile as wavfile
from unittest.mock import patch, MagicMock
from src.whisper_service import WhisperService

class TestWhisperService:

    @pytest.fixture
    def whisper_service(self):
        return WhisperService(model_size="base", device="cpu")

    @pytest.fixture
    def sample_audio_file(self):
        # Generate synthetic audio for testing
        sample_rate = 16000
        duration = 2  # seconds
        frequency = 440  # Hz (A note)

        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = np.sin(2 * np.pi * frequency * t)
        audio_data = (audio_data * 32767).astype(np.int16)

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            wavfile.write(f.name, sample_rate, audio_data)
            return f.name

    def test_transcribe_success(self, whisper_service, sample_audio_file):
        with patch.object(whisper_service.model, 'transcribe') as mock_transcribe:
            # Mock successful transcription
            mock_segment = MagicMock()
            mock_segment.text = "Hello world"
            mock_info = MagicMock()
            mock_info.language = "en"
            mock_info.language_probability = 0.95
            mock_info.duration = 2.0

            mock_transcribe.return_value = ([mock_segment], mock_info)

            result = whisper_service.transcribe(sample_audio_file)

            assert result["text"] == "Hello world"
            assert result["language"] == "en"
            assert result["language_probability"] == 0.95
            assert result["duration"] == 2.0
            assert result["word_count"] == 2

    def test_transcribe_empty_audio(self, whisper_service):
        with patch.object(whisper_service.model, 'transcribe') as mock_transcribe:
            mock_info = MagicMock()
            mock_info.language = "en"
            mock_info.language_probability = 0.5
            mock_info.duration = 0.0

            mock_transcribe.return_value = ([], mock_info)

            result = whisper_service.transcribe("empty.wav")

            assert result["text"] == ""
            assert result["word_count"] == 0

    def test_transcribe_multilingual(self, whisper_service, sample_audio_file):
        with patch.object(whisper_service.model, 'transcribe') as mock_transcribe:
            mock_segment = MagicMock()
            mock_segment.text = "Bonjour le monde"
            mock_info = MagicMock()
            mock_info.language = "fr"
            mock_info.language_probability = 0.88
            mock_info.duration = 2.5

            mock_transcribe.return_value = ([mock_segment], mock_info)

            result = whisper_service.transcribe(sample_audio_file)

            assert result["language"] == "fr"
            assert "Bonjour" in result["text"]

    def test_transcribe_error_handling(self, whisper_service):
        with patch.object(whisper_service.model, 'transcribe') as mock_transcribe:
            mock_transcribe.side_effect = Exception("Model error")

            with pytest.raises(Exception, match="Model error"):
                whisper_service.transcribe("nonexistent.wav")

    @pytest.mark.parametrize("language,expected_prob", [
        ("en", 0.95),
        ("es", 0.87),
        ("fr", 0.82),
        ("de", 0.79)
    ])
    def test_language_detection_accuracy(self, whisper_service, sample_audio_file, language, expected_prob):
        with patch.object(whisper_service.model, 'transcribe') as mock_transcribe:
            mock_segment = MagicMock()
            mock_segment.text = "Test text"
            mock_info = MagicMock()
            mock_info.language = language
            mock_info.language_probability = expected_prob
            mock_info.duration = 1.0

            mock_transcribe.return_value = ([mock_segment], mock_info)

            result = whisper_service.transcribe(sample_audio_file)

            assert result["language"] == language
            assert result["language_probability"] >= 0.7  # Minimum confidence threshold
```

### 2.3 LLM Structured Output & Function Calling Tests

#### Service Implementation (`src/ollama_service.py`)
```python
import requests
import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, ValidationError
import logging

class OllamaService:
    def __init__(self, host: str = "http://localhost:11434", model: str = "phi4"):
        self.host = host
        self.model = model
        self.logger = logging.getLogger(__name__)

    def generate_structured(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "format": schema,
            "stream": False
        }

        response = requests.post(f"{self.host}/api/chat", json=payload)
        response.raise_for_status()

        result = response.json()
        return json.loads(result["message"]["content"])

    def function_call(self, prompt: str, tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "tools": tools,
            "stream": False
        }

        response = requests.post(f"{self.host}/api/chat", json=payload)
        response.raise_for_status()

        return response.json()

    def health_check(self) -> bool:
        try:
            response = requests.get(f"{self.host}/api/version", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
```

#### Schema Definitions (`src/schemas.py`)
```python
from pydantic import BaseModel
from typing import List, Optional

class WeatherResponse(BaseModel):
    location: str
    temperature: float
    condition: str
    humidity: Optional[int] = None

class PersonInfo(BaseModel):
    name: str
    age: int
    occupation: Optional[str] = None
    skills: List[str] = []

class FunctionCall(BaseModel):
    name: str
    parameters: Dict[str, Any]
```

#### Test Implementation (`tests/test_ollama.py`)
```python
import pytest
import requests_mock
from unittest.mock import patch
from src.ollama_service import OllamaService
from src.schemas import WeatherResponse, PersonInfo

class TestOllamaService:

    @pytest.fixture
    def ollama_service(self):
        return OllamaService()

    @pytest.fixture
    def weather_schema(self):
        return {
            "type": "object",
            "properties": {
                "location": {"type": "string"},
                "temperature": {"type": "number"},
                "condition": {"type": "string"},
                "humidity": {"type": "number"}
            },
            "required": ["location", "temperature", "condition"]
        }

    def test_structured_output_success(self, ollama_service, weather_schema):
        with requests_mock.Mocker() as m:
            mock_response = {
                "message": {
                    "content": '{"location": "Paris", "temperature": 22.5, "condition": "sunny", "humidity": 65}'
                },
                "done": True
            }

            m.post("http://localhost:11434/api/chat", json=mock_response)

            result = ollama_service.generate_structured(
                "What's the weather in Paris?",
                weather_schema
            )

            weather = WeatherResponse(**result)
            assert weather.location == "Paris"
            assert weather.temperature == 22.5
            assert weather.condition == "sunny"
            assert weather.humidity == 65

    def test_function_calling_success(self, ollama_service):
        tools = [{
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get weather information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string"}
                    },
                    "required": ["location"]
                }
            }
        }]

        with requests_mock.Mocker() as m:
            mock_response = {
                "message": {
                    "tool_calls": [
                        {
                            "function": {
                                "name": "get_weather",
                                "arguments": {"location": "London"}
                            }
                        }
                    ]
                },
                "done": True
            }

            m.post("http://localhost:11434/api/chat", json=mock_response)

            result = ollama_service.function_call(
                "What's the weather in London?",
                tools
            )

            tool_calls = result["message"]["tool_calls"]
            assert len(tool_calls) == 1
            assert tool_calls[0]["function"]["name"] == "get_weather"
            assert tool_calls[0]["function"]["arguments"]["location"] == "London"

    def test_health_check_success(self, ollama_service):
        with requests_mock.Mocker() as m:
            m.get("http://localhost:11434/api/version", json={"version": "0.9.6"})

            assert ollama_service.health_check() is True

    def test_health_check_failure(self, ollama_service):
        with requests_mock.Mocker() as m:
            m.get("http://localhost:11434/api/version", status_code=500)

            assert ollama_service.health_check() is False

    @pytest.mark.parametrize("invalid_json", [
        '{"location": "Paris", "temperature":}',  # Invalid JSON
        '{"location": "Paris"}',  # Missing required fields
        'Not JSON at all'  # Not JSON
    ])
    def test_structured_output_validation_errors(self, ollama_service, weather_schema, invalid_json):
        with requests_mock.Mocker() as m:
            mock_response = {
                "message": {"content": invalid_json},
                "done": True
            }

            m.post("http://localhost:11434/api/chat", json=mock_response)

            with pytest.raises((json.JSONDecodeError, ValueError)):
                ollama_service.generate_structured(
                    "What's the weather?",
                    weather_schema
                )
```

### 2.4 Integration Tests

#### Implementation (`tests/test_integration.py`)
```python
import pytest
import tempfile
import time
from src.whisper_service import WhisperService
from src.ollama_service import OllamaService

class TestIntegration:

    @pytest.fixture(scope="session")
    def services(self):
        # Wait for services to be ready
        ollama = OllamaService()
        for _ in range(30):  # Wait up to 30 seconds
            if ollama.health_check():
                break
            time.sleep(1)
        else:
            pytest.skip("Ollama service not available")

        return {
            "whisper": WhisperService(),
            "ollama": ollama
        }

    def test_audio_to_structured_summary(self, services, sample_audio_file):
        # Step 1: Transcribe audio
        transcript_result = services["whisper"].transcribe(sample_audio_file)

        # Step 2: Analyze transcript with LLM
        analysis_prompt = f"""
        Analyze this transcript and extract key information:
        "{transcript_result['text']}"

        Provide a structured summary.
        """

        schema = {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "key_points": {"type": "array", "items": {"type": "string"}},
                "sentiment": {"type": "string", "enum": ["positive", "negative", "neutral"]},
                "word_count": {"type": "number"}
            },
            "required": ["summary", "sentiment", "word_count"]
        }

        analysis = services["ollama"].generate_structured(analysis_prompt, schema)

        # Assertions
        assert "summary" in analysis
        assert "sentiment" in analysis
        assert analysis["sentiment"] in ["positive", "negative", "neutral"]
        assert isinstance(analysis["word_count"], (int, float))

    def test_end_to_end_performance(self, services, sample_audio_file):
        start_time = time.time()

        # Transcription
        transcript_start = time.time()
        transcript = services["whisper"].transcribe(sample_audio_file)
        transcript_time = time.time() - transcript_start

        # LLM Processing
        llm_start = time.time()
        schema = {
            "type": "object",
            "properties": {
                "processed": {"type": "boolean"},
                "timestamp": {"type": "string"}
            }
        }

        llm_result = services["ollama"].generate_structured(
            f"Process this text: {transcript['text'][:100]}",
            schema
        )
        llm_time = time.time() - llm_start

        total_time = time.time() - start_time

        # Performance assertions
        assert transcript_time < 30  # Transcription should complete in 30s
        assert llm_time < 15  # LLM should respond in 15s
        assert total_time < 45  # Total pipeline under 45s

        # Results validation
        assert transcript["text"] is not None
        assert llm_result["processed"] is True
```

### 2.5 Test Configuration

#### pytest Configuration (`pytest.ini`)
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --tb=short
    --strict-markers
    --disable-warnings
    --cov=src
    --cov-report=html
    --cov-report=term-missing
markers =
    slow: marks tests as slow
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

#### Test Fixtures (`tests/conftest.py`)
```python
import pytest
import tempfile
import numpy as np
import scipy.io.wavfile as wavfile

@pytest.fixture(scope="session")
def sample_audio_file():
    """Generate a sample audio file for testing"""
    sample_rate = 16000
    duration = 3
    frequency = 440

    t = np.linspace(0, duration, int(sample_rate * duration))
    audio_data = np.sin(2 * np.pi * frequency * t)
    audio_data = (audio_data * 32767).astype(np.int16)

    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
        wavfile.write(f.name, sample_rate, audio_data)
        return f.name

@pytest.fixture
def mock_whisper_response():
    return {
        "text": "Hello, this is a test transcription.",
        "language": "en",
        "language_probability": 0.95,
        "duration": 3.0,
        "word_count": 7
    }

@pytest.fixture
def mock_ollama_response():
    return {
        "message": {
            "content": '{"status": "success", "processed": true}'
        },
        "done": True
    }
```

## Phase 3: Integration & Validation (1 hour)

### 3.1 Deployment Validation
```bash
# Run complete test suite
pytest tests/ -v --cov=src

# Performance benchmarking
pytest tests/test_integration.py::TestIntegration::test_end_to_end_performance -v

# Generate coverage report
pytest --cov=src --cov-report=html
```

### 3.2 Service Health Checks
```bash
# Check Docker containers
docker compose ps
docker compose logs ollama

# Test API endpoints
curl http://localhost:11434/api/version
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "phi4", "prompt": "Hello", "stream": false}'
```

## Expected Results & Performance Benchmarks

### Whisper Performance
- **Transcription Speed**: 2-4x faster than original Whisper
- **Memory Usage**: ~2-4GB for base model
- **Accuracy**: WER < 10% for clean English audio

### Ollama/Phi-4-Mini Performance
- **Response Time**: 2-5 seconds for structured outputs
- **Memory Usage**: ~4-6GB for loaded model
- **Token Throughput**: 20-50 tokens/second

### Testing Coverage
- **Unit Tests**: >90% code coverage
- **Integration Tests**: End-to-end functionality
- **Performance Tests**: Latency and throughput validation

## Troubleshooting Guide

### Common Issues

**Docker Installation Issues:**
- Permission denied: Run `sudo usermod -aG docker $USER` and restart
- Service not starting: Check `sudo systemctl status docker`

**Whisper Issues:**
- CUDA not detected: Verify GPU drivers and CUDA installation
- Memory errors: Use smaller model or CPU-only mode

**Ollama Issues:**
- Model not loading: Check available memory (8GB+ recommended for Phi-4)
- Connection refused: Verify container is running on port 11434
- Slow responses: Consider quantized model variants

**Testing Issues:**
- Import errors: Ensure virtual environment is activated
- Timeout errors: Increase test timeout values
- Audio file issues: Check sample rate and format compatibility

### Optimization Tips

1. **Memory Optimization:**
   - Use quantized models (Q4_K_M, Q8_0)
   - Implement model unloading after use
   - Monitor memory usage with `docker stats`

2. **Performance Tuning:**
   - Enable GPU acceleration where available
   - Use appropriate batch sizes for processing
   - Implement caching for repeated requests

3. **Testing Optimization:**
   - Use mocks for unit tests to reduce execution time
   - Run integration tests in CI/CD pipeline only
   - Implement test data cleanup procedures

## Next Steps

1. **Production Deployment:**
   - Add authentication and rate limiting
   - Implement monitoring and logging
   - Set up automated backups

2. **Enhanced Features:**
   - Real-time streaming transcription
   - Multi-model support
   - Custom model fine-tuning

3. **Scalability:**
   - Kubernetes deployment
   - Load balancing
   - Horizontal scaling strategies

---
