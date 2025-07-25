# AI Services Test Framework

[![Tests](https://img.shields.io/badge/tests-36%2F36%20passing-brightgreen)](https://github.com/aphlox/ai-services-test-framework)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/python-3.8+-blue)](https://www.python.org/)

A comprehensive testing framework for AI services featuring Docker containerization, Whisper speech-to-text transcription, Ollama LLM integration, and full unit/integration testing suite.

## 🚀 Features

- **🎤 Whisper Transcription Service** - OpenAI Whisper with multi-language support
- **🤖 Ollama LLM Integration** - Containerized LLM with structured output and function calling
- **🐳 Docker Containerization** - Full containerized deployment with resource management  
- **🧪 Comprehensive Testing** - 36 tests with 100% pass rate and coverage reporting
- **📊 Performance Monitoring** - Memory usage tracking and benchmark validation
- **🔧 Production Ready** - Error handling, logging, and health checks

## 📋 Requirements

- **System**: WSL2 Linux or Ubuntu 20.04+
- **Memory**: 8GB+ RAM available  
- **Storage**: 5GB+ free space
- **Python**: 3.8+
- **Docker**: Latest version with Docker Compose

## ⚡ Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/aphlox/ai-services-test-framework.git
cd ai-services-test-framework
```

### 2. Setup Environment
```bash
# Create Python virtual environment
python3 -m venv whisper-env
source whisper-env/bin/activate

# Install dependencies
pip install -r ai-services-testing/requirements.txt

# Install system dependencies (Ubuntu/Debian)
sudo apt install ffmpeg
```

### 3. Start Services
```bash
# Start Docker containers
docker-compose up -d

# Verify services
python ai-services-testing/validation_test.py
```

### 4. Run Tests
```bash
cd ai-services-testing
pytest tests/ -v --cov=src --cov-report=html
```

## 🏗️ Architecture

```
ai-services-testing/
├── src/
│   ├── whisper_service.py      # Whisper transcription service
│   ├── ollama_service.py       # Ollama LLM service  
│   └── schemas.py              # Pydantic data models
├── tests/
│   ├── conftest.py             # Test fixtures
│   ├── test_whisper.py         # Whisper unit tests (12 tests)
│   ├── test_ollama.py          # Ollama unit tests (16 tests)
│   └── test_integration.py     # Integration tests (8 tests)
├── requirements.txt            # Python dependencies
├── pytest.ini                 # Test configuration
└── validation_test.py          # System validation
```

## 🎯 Services

### Whisper Transcription
```python
from src.whisper_service import WhisperService

whisper = WhisperService(model_size="base", device="cpu")
result = whisper.transcribe("audio_file.wav")
print(f"Transcribed: {result['text']}")
```

### Ollama LLM  
```python
from src.ollama_service import OllamaService

ollama = OllamaService()
health = ollama.health_check()  # Check if service is ready
response = ollama.simple_generate("Hello, how are you?")
```

## 🧪 Testing

### Test Coverage
- **Unit Tests**: 28/28 passing (100%)
- **Integration Tests**: 8/8 passing (100%) 
- **Total Coverage**: 36/36 tests passing

### Test Categories
- **Functional Tests**: Core service functionality testing
- **Performance Tests**: Speed and memory benchmark validation
- **Error Handling**: Exception scenarios and recovery testing
- **Integration Tests**: End-to-end pipeline validation

### Running Tests
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src --cov-report=html

# Run specific test categories  
pytest tests/ -m integration
pytest tests/ -m "not slow"
```

## 📊 Performance Benchmarks

| Metric | Target | Achieved |
|--------|--------|----------|
| Whisper Transcription | <30s processing | ✅ 3.6s |
| Memory Usage | <4GB | ✅ ~1.5GB |
| Ollama Response | <15s | ✅ <1s |
| Test Suite Runtime | <30s | ✅ ~11s |

## 🐳 Docker Services

### Start Services
```bash
docker-compose up -d
```

### Check Status  
```bash
docker-compose ps
docker-compose logs ollama
```

### API Endpoints
- **Ollama API**: http://localhost:11434
- **Health Check**: http://localhost:11434/api/version

## 📈 Monitoring

### System Validation
```bash
python validation_test.py
```

### Container Health
```bash
docker stats
docker-compose logs --tail=20 ollama
```

## 🔧 Configuration

### Environment Variables
```bash
# Ollama Configuration
OLLAMA_KEEP_ALIVE=5m
OLLAMA_HOST=0.0.0.0
OLLAMA_MAX_LOADED_MODELS=1

# Whisper Configuration  
WHISPER_MODEL=base
WHISPER_DEVICE=cpu
```

### Resource Limits
- **Ollama Container**: 8GB memory, 4 CPU cores
- **Whisper Service**: ~2GB memory usage
- **Total System**: <17GB memory recommended

## 🚨 Troubleshooting

### Common Issues

**Docker Issues:**
```bash
# Check Docker status
docker --version
docker-compose --version

# Restart services
docker-compose down && docker-compose up -d
```

**Python Issues:**
```bash
# Ensure virtual environment is active
source whisper-env/bin/activate

# Reinstall dependencies
pip install -r ai-services-testing/requirements.txt
```

**Audio Issues:**
```bash
# Install ffmpeg
sudo apt install ffmpeg

# Test audio processing
ffmpeg -version
```

## 📚 Documentation

- [Implementation Results](IMPLEMENTATION_RESULTS.md) - Detailed implementation report
- [Technical Specifications](Technical_Specs.md) - System architecture details  
- [Implementation Timeline](IMPLEMENTATION_TIMELINE.md) - Development milestones
- [Setup Plan](AI_Services_Setup_Plan.md) - Original implementation plan

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`pytest tests/ -v`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏆 Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) for speech recognition
- [Ollama](https://ollama.ai/) for LLM integration
- [Docker](https://www.docker.com/) for containerization
- [pytest](https://pytest.org/) for testing framework

---

**Built with ❤️ for AI service testing and validation**