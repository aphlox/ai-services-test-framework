import pytest
import tempfile
import numpy as np
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

@pytest.fixture(scope="session")
def sample_audio_file():
    """Generate a sample audio file for testing"""
    try:
        import scipy.io.wavfile as wavfile
        
        sample_rate = 16000
        duration = 3  # seconds
        frequency = 440  # Hz (A note)

        t = np.linspace(0, duration, int(sample_rate * duration))
        # Create a simple sine wave
        audio_data = np.sin(2 * np.pi * frequency * t)
        # Convert to 16-bit integer
        audio_data = (audio_data * 32767).astype(np.int16)

        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            wavfile.write(f.name, sample_rate, audio_data)
            yield f.name
            
        # Cleanup
        try:
            os.unlink(f.name)
        except:
            pass
            
    except ImportError:
        # If scipy is not available, create a dummy file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            f.write(b'dummy audio data')
            yield f.name
        try:
            os.unlink(f.name)
        except:
            pass

@pytest.fixture
def mock_whisper_response():
    """Mock response from Whisper transcription"""
    return {
        "text": "Hello, this is a test transcription.",
        "language": "en",
        "language_probability": 0.95,
        "duration": 3.0,
        "word_count": 7,
        "processing_time": 1.5
    }

@pytest.fixture
def mock_ollama_response():
    """Mock response from Ollama"""
    return {
        "message": {
            "content": '{"status": "success", "processed": true}'
        },
        "done": True
    }

@pytest.fixture
def weather_schema():
    """Sample weather schema for structured output testing"""
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

@pytest.fixture
def sample_tools():
    """Sample tools for function calling tests"""
    return [{
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