import pytest
import requests
import requests_mock
import json
from unittest.mock import patch
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ollama_service import OllamaService
from schemas import WeatherResponse, PersonInfo

class TestOllamaService:

    @pytest.fixture
    def ollama_service(self):
        return OllamaService()

    def test_ollama_service_init(self, ollama_service):
        """Test OllamaService initialization"""
        assert ollama_service.host == "http://localhost:11434"
        assert ollama_service.model == "phi3"

    def test_health_check_success(self, ollama_service):
        """Test successful health check"""
        with requests_mock.Mocker() as m:
            m.get("http://localhost:11434/api/version", json={"version": "0.9.6"})

            assert ollama_service.health_check() is True

    def test_health_check_failure(self, ollama_service):
        """Test failed health check"""
        with requests_mock.Mocker() as m:
            m.get("http://localhost:11434/api/version", status_code=500)

            assert ollama_service.health_check() is False

    def test_health_check_timeout(self, ollama_service):
        """Test health check timeout"""
        with requests_mock.Mocker() as m:
            m.get("http://localhost:11434/api/version", exc=requests.exceptions.Timeout)

            assert ollama_service.health_check() is False

    def test_structured_output_success(self, ollama_service, weather_schema):
        """Test successful structured output generation"""
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

            # Validate with Pydantic model
            weather = WeatherResponse(**result)
            assert weather.location == "Paris"
            assert weather.temperature == 22.5
            assert weather.condition == "sunny"
            assert weather.humidity == 65

    def test_structured_output_invalid_json(self, ollama_service, weather_schema):
        """Test handling of invalid JSON in structured output"""
        with requests_mock.Mocker() as m:
            mock_response = {
                "message": {
                    "content": "This is not JSON"
                },
                "done": True
            }

            m.post("http://localhost:11434/api/chat", json=mock_response)

            result = ollama_service.generate_structured(
                "What's the weather?",
                weather_schema
            )

            # Should return text content when JSON parsing fails
            assert result == {"text": "This is not JSON"}

    def test_function_calling_success(self, ollama_service, sample_tools):
        """Test successful function calling"""
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
                sample_tools
            )

            tool_calls = result["message"]["tool_calls"]
            assert len(tool_calls) == 1
            assert tool_calls[0]["function"]["name"] == "get_weather"
            assert tool_calls[0]["function"]["arguments"]["location"] == "London"

    def test_simple_generate_success(self, ollama_service):
        """Test simple text generation"""
        with requests_mock.Mocker() as m:
            mock_response = {
                "response": "Hello! How can I help you today?",
                "done": True
            }

            m.post("http://localhost:11434/api/generate", json=mock_response)

            result = ollama_service.simple_generate("Hello")

            assert result == "Hello! How can I help you today?"

    def test_list_models_success(self, ollama_service):
        """Test listing available models"""
        with requests_mock.Mocker() as m:
            mock_response = {
                "models": [
                    {"name": "phi3:latest"},
                    {"name": "llama2:7b"},
                    {"name": "codellama:13b"}
                ]
            }

            m.get("http://localhost:11434/api/tags", json=mock_response)

            models = ollama_service.list_models()

            assert "phi3:latest" in models
            assert "llama2:7b" in models
            assert "codellama:13b" in models
            assert len(models) == 3

    def test_list_models_empty(self, ollama_service):
        """Test listing models when none are available"""
        with requests_mock.Mocker() as m:
            mock_response = {"models": []}

            m.get("http://localhost:11434/api/tags", json=mock_response)

            models = ollama_service.list_models()

            assert models == []

    def test_list_models_error(self, ollama_service):
        """Test error handling when listing models fails"""
        with requests_mock.Mocker() as m:
            m.get("http://localhost:11434/api/tags", status_code=500)

            models = ollama_service.list_models()

            assert models == []

    @pytest.mark.parametrize("invalid_json", [
        '{"location": "Paris", "temperature":}',  # Invalid JSON
        '{"location": "Paris"}',  # Missing required fields  
        'Not JSON at all'  # Not JSON
    ])
    def test_structured_output_validation_errors(self, ollama_service, weather_schema, invalid_json):
        """Test handling of various invalid JSON scenarios"""
        with requests_mock.Mocker() as m:
            mock_response = {
                "message": {"content": invalid_json},
                "done": True
            }

            m.post("http://localhost:11434/api/chat", json=mock_response)

            result = ollama_service.generate_structured(
                "What's the weather?",
                weather_schema
            )

            # Should handle gracefully and return text content
            if invalid_json == 'Not JSON at all':
                assert result == {"text": invalid_json}
            else:
                # For invalid JSON, should still attempt parsing but may fail
                # The service should handle this gracefully
                assert isinstance(result, dict)

    def test_request_timeout_handling(self, ollama_service):
        """Test handling of request timeouts"""
        with requests_mock.Mocker() as m:
            m.post("http://localhost:11434/api/generate", exc=requests.exceptions.Timeout)

            with pytest.raises(requests.exceptions.Timeout):
                ollama_service.simple_generate("Hello")

    def test_connection_error_handling(self, ollama_service):
        """Test handling of connection errors"""
        with requests_mock.Mocker() as m:
            m.post("http://localhost:11434/api/generate", exc=requests.exceptions.ConnectionError)

            with pytest.raises(requests.exceptions.ConnectionError):
                ollama_service.simple_generate("Hello")