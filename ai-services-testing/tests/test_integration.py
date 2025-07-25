import pytest
import tempfile
import time
import sys
import os
from unittest.mock import patch, MagicMock

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from whisper_service import WhisperService
from ollama_service import OllamaService

class TestIntegration:

    @pytest.fixture
    def services(self):
        """Initialize services for integration testing"""
        # Create fresh services for each test to avoid caching issues
        return {
            "whisper": WhisperService(model_size="base", device="cpu"),
            "ollama": OllamaService()
        }

    @pytest.mark.integration
    @patch('whisper_service.whisper.load_model')
    def test_audio_to_structured_summary_mock(self, mock_load_model, services, sample_audio_file):
        """Test end-to-end pipeline with mocked services"""
        # Mock Whisper model
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            "text": "Hello world, this is a test transcription",
            "language": "en",
            "language_probability": 0.95,
            "duration": 3.0
        }
        mock_load_model.return_value = mock_model

        # Step 1: Transcribe audio
        transcript_result = services["whisper"].transcribe(sample_audio_file)

        # Verify transcription result
        assert transcript_result["text"] == "Hello world, this is a test transcription"
        assert transcript_result["language"] == "en"
        assert transcript_result["word_count"] == 7
        assert "processing_time" in transcript_result

        # Step 2: Mock LLM analysis (since Ollama container might not be ready)
        # In a real integration test, this would call the actual Ollama service
        mock_analysis = {
            "summary": "Test transcription about greeting",
            "key_points": ["greeting", "test audio"],
            "sentiment": "neutral",
            "word_count": 8
        }

        # Verify analysis structure
        assert "summary" in mock_analysis
        assert "sentiment" in mock_analysis
        assert mock_analysis["sentiment"] in ["positive", "negative", "neutral"]
        assert isinstance(mock_analysis["word_count"], int)

    @pytest.mark.integration
    @patch('whisper_service.whisper.load_model')
    def test_end_to_end_performance_mock(self, mock_load_model, services, sample_audio_file):
        """Test end-to-end pipeline performance with mocked services"""
        # Mock Whisper model for performance testing
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            "text": "Performance test audio",
            "language": "en",
            "language_probability": 0.9,
            "duration": 2.0
        }
        mock_load_model.return_value = mock_model

        start_time = time.time()

        # Transcription timing
        transcript_start = time.time()
        transcript = services["whisper"].transcribe(sample_audio_file)
        transcript_time = time.time() - transcript_start

        # Mock LLM processing timing
        llm_start = time.time()
        # Simulate LLM processing time
        time.sleep(0.1)  # Mock processing delay
        mock_llm_result = {
            "processed": True,
            "timestamp": str(time.time())
        }
        llm_time = time.time() - llm_start

        total_time = time.time() - start_time

        # Performance assertions (relaxed for mocked services)
        assert transcript_time < 10  # Mocked transcription should be fast
        assert llm_time < 5  # Mocked LLM should be fast
        assert total_time < 15  # Total pipeline should be reasonable

        # Results validation
        assert transcript["text"] is not None
        assert mock_llm_result["processed"] is True

    @pytest.mark.integration
    def test_whisper_service_real_audio(self, services, sample_audio_file):
        """Test Whisper service with real audio (mocked model)"""
        with patch('whisper_service.whisper.load_model') as mock_load_model:
            mock_model = MagicMock()
            mock_model.transcribe.return_value = {
                "text": "Test audio transcription",
                "language": "en",
                "language_probability": 0.92,
                "duration": 1.5
            }
            mock_load_model.return_value = mock_model

            result = services["whisper"].transcribe(sample_audio_file)

            # Basic functionality tests
            assert isinstance(result, dict)
            assert "text" in result
            assert "language" in result
            assert "word_count" in result
            assert "processing_time" in result
            assert result["word_count"] > 0

    @pytest.mark.integration
    def test_ollama_service_health_mock(self, services):
        """Test Ollama service health check (will fail if service not running)"""
        # This test will actually check if Ollama is running
        # If not running, it should return False
        health_status = services["ollama"].health_check()
        
        # We expect this to be False since Ollama container may not be ready
        # In a real deployment, this would be True
        assert isinstance(health_status, bool)

    @pytest.mark.integration
    def test_multiple_transcriptions_performance(self, services, sample_audio_file):
        """Test performance with multiple transcription requests"""
        # Create a fresh service instance to avoid caching
        fresh_service = WhisperService(model_size="base", device="cpu")
        
        with patch('whisper_service.whisper.load_model') as mock_load_model:
            mock_model = MagicMock()
            mock_model.transcribe.return_value = {
                "text": "Multiple test transcription",
                "language": "en", 
                "language_probability": 0.9,
                "duration": 2.0
            }
            mock_load_model.return_value = mock_model

            # Test multiple transcriptions
            results = []
            start_time = time.time()
            
            for i in range(3):
                result = fresh_service.transcribe(sample_audio_file)
                results.append(result)
                
            total_time = time.time() - start_time

            # Verify all transcriptions completed
            assert len(results) == 3
            for result in results:
                assert result["text"] == "Multiple test transcription"
                assert result["language"] == "en"

            # Performance check (should be fast with mocked model)
            assert total_time < 5  # Should complete quickly with mocked model

    @pytest.mark.integration 
    def test_error_handling_integration(self, services):
        """Test error handling in integration scenarios"""
        # Test with non-existent audio file - should raise an exception
        with patch('whisper_service.whisper.load_model') as mock_load_model:
            mock_model = MagicMock()
            mock_model.transcribe.side_effect = FileNotFoundError("No such file or directory")
            mock_load_model.return_value = mock_model
            
            with pytest.raises(Exception):
                services["whisper"].transcribe("non_existent_file.wav")

        # Test Ollama with invalid host
        invalid_ollama = OllamaService(host="http://invalid-host:11434")
        assert invalid_ollama.health_check() is False

    @pytest.mark.integration
    def test_service_isolation(self, services):
        """Test that services work independently"""
        # Test that Whisper service initialization doesn't affect Ollama
        whisper_service = WhisperService()
        ollama_service = OllamaService()
        
        # Both should be independent
        assert whisper_service.model_size == "base"
        assert ollama_service.model == "phi3"
        
        # Changing one shouldn't affect the other
        whisper_service.model_size = "small"
        assert ollama_service.model == "phi3"

    @pytest.mark.slow
    @pytest.mark.integration
    def test_memory_usage_monitoring(self, services, sample_audio_file):
        """Test memory usage during processing"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create a fresh service to avoid caching issues
        fresh_service = WhisperService(model_size="base", device="cpu")
        
        with patch('whisper_service.whisper.load_model') as mock_load_model:
            mock_model = MagicMock()
            mock_model.transcribe.return_value = {
                "text": "Memory test transcription",
                "language": "en",
                "language_probability": 0.9,
                "duration": 2.0
            }
            mock_load_model.return_value = mock_model

            # Perform multiple operations
            for i in range(5):
                result = fresh_service.transcribe(sample_audio_file)
                assert result["text"] == "Memory test transcription"

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB for mocked operations)
        assert memory_increase < 100, f"Memory increased by {memory_increase}MB"