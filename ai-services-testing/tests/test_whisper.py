import pytest
import tempfile
import numpy as np
from unittest.mock import patch, MagicMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from whisper_service import WhisperService

class TestWhisperService:

    @pytest.fixture
    def whisper_service(self):
        return WhisperService(model_size="base", device="cpu")

    def test_whisper_service_init(self, whisper_service):
        """Test WhisperService initialization"""
        assert whisper_service.model_size == "base"
        assert whisper_service.device == "cpu"
        assert whisper_service.model is None

    @patch('whisper_service.whisper.load_model')
    def test_model_loading(self, mock_load_model, whisper_service):
        """Test lazy model loading"""
        mock_model = MagicMock()
        mock_load_model.return_value = mock_model
        
        # Model should not be loaded initially
        assert whisper_service.model is None
        
        # Force model loading
        whisper_service._load_model()
        
        # Model should now be loaded
        assert whisper_service.model == mock_model
        mock_load_model.assert_called_once_with("base", device="cpu")

    @patch('whisper_service.whisper.load_model')
    def test_transcribe_success(self, mock_load_model, whisper_service, sample_audio_file):
        """Test successful transcription"""
        # Mock the model and its transcribe method
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            "text": "Hello world",
            "language": "en",
            "language_probability": 0.95,
            "duration": 2.0
        }
        mock_load_model.return_value = mock_model

        result = whisper_service.transcribe(sample_audio_file)

        assert result["text"] == "Hello world"
        assert result["language"] == "en"
        assert result["language_probability"] == 0.95
        assert result["duration"] == 2.0
        assert result["word_count"] == 2
        assert "processing_time" in result

    @patch('whisper_service.whisper.load_model')
    def test_transcribe_empty_audio(self, mock_load_model, whisper_service, sample_audio_file):
        """Test transcription of empty/silent audio"""
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            "text": "",
            "language": "en",
            "language_probability": 0.5,
            "duration": 0.0
        }
        mock_load_model.return_value = mock_model

        result = whisper_service.transcribe(sample_audio_file)

        assert result["text"] == ""
        assert result["word_count"] == 0

    @patch('whisper_service.whisper.load_model')
    def test_transcribe_multilingual(self, mock_load_model, whisper_service, sample_audio_file):
        """Test multilingual transcription"""
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            "text": "Bonjour le monde",
            "language": "fr",
            "language_probability": 0.88,
            "duration": 2.5
        }
        mock_load_model.return_value = mock_model

        result = whisper_service.transcribe(sample_audio_file)

        assert result["language"] == "fr"
        assert "Bonjour" in result["text"]
        assert result["language_probability"] == 0.88

    @patch('whisper_service.whisper.load_model')
    def test_transcribe_error_handling(self, mock_load_model, whisper_service):
        """Test error handling during transcription"""
        mock_model = MagicMock()
        mock_model.transcribe.side_effect = Exception("Model error")
        mock_load_model.return_value = mock_model

        with pytest.raises(Exception, match="Model error"):
            whisper_service.transcribe("nonexistent.wav")

    @pytest.mark.parametrize("language,expected_prob", [
        ("en", 0.95),
        ("es", 0.87),
        ("fr", 0.82),
        ("de", 0.79)
    ])
    @patch('whisper_service.whisper.load_model')
    def test_language_detection_accuracy(self, mock_load_model, whisper_service, 
                                       sample_audio_file, language, expected_prob):
        """Test language detection accuracy for different languages"""
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            "text": "Test text",
            "language": language,
            "language_probability": expected_prob,
            "duration": 1.0
        }
        mock_load_model.return_value = mock_model

        result = whisper_service.transcribe(sample_audio_file)

        assert result["language"] == language
        assert result["language_probability"] >= 0.7  # Minimum confidence threshold

    def test_get_available_models(self, whisper_service):
        """Test getting list of available models"""
        models = whisper_service.get_available_models()
        
        expected_models = ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"]
        assert models == expected_models

    @patch('whisper_service.whisper.load_model')
    def test_model_caching(self, mock_load_model, whisper_service, sample_audio_file):
        """Test that model is loaded only once (caching)"""
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            "text": "Test",
            "language": "en",
            "language_probability": 0.9,
            "duration": 1.0
        }
        mock_load_model.return_value = mock_model

        # Call transcribe twice
        whisper_service.transcribe(sample_audio_file)
        whisper_service.transcribe(sample_audio_file)

        # Model should be loaded only once
        mock_load_model.assert_called_once()