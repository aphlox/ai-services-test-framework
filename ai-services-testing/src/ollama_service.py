import requests
import json
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, ValidationError
import logging
import time

class OllamaService:
    def __init__(self, host: str = "http://localhost:11434", model: str = "phi3"):
        self.host = host
        self.model = model
        self.logger = logging.getLogger(__name__)

    def generate_structured(self, prompt: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate structured JSON response from LLM
        
        Args:
            prompt: Input prompt
            schema: JSON schema for structured output
            
        Returns:
            Structured response as dict
        """
        try:
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "format": schema,
                "stream": False
            }

            response = requests.post(f"{self.host}/api/chat", json=payload, timeout=30)
            response.raise_for_status()

            result = response.json()
            content = result["message"]["content"]
            
            # Parse JSON response
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # If not valid JSON, return as text
                return {"text": content}
                
        except Exception as e:
            self.logger.error(f"Structured generation failed: {e}")
            raise

    def function_call(self, prompt: str, tools: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Execute function calling with LLM
        
        Args:
            prompt: Input prompt
            tools: List of available tools/functions
            
        Returns:
            Function call response
        """
        try:
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "tools": tools,
                "stream": False
            }

            response = requests.post(f"{self.host}/api/chat", json=payload, timeout=30)
            response.raise_for_status()

            return response.json()
            
        except Exception as e:
            self.logger.error(f"Function call failed: {e}")
            raise

    def simple_generate(self, prompt: str) -> str:
        """
        Simple text generation
        
        Args:
            prompt: Input prompt
            
        Returns:
            Generated text response
        """
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False
            }

            response = requests.post(f"{self.host}/api/generate", json=payload, timeout=30)
            response.raise_for_status()

            result = response.json()
            return result.get("response", "")
            
        except Exception as e:
            self.logger.error(f"Text generation failed: {e}")
            raise

    def health_check(self) -> bool:
        """
        Check if Ollama service is healthy
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            response = requests.get(f"{self.host}/api/version", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
            
    def list_models(self) -> List[str]:
        """
        List available models
        
        Returns:
            List of model names
        """
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=10)
            response.raise_for_status()
            
            result = response.json()
            return [model["name"] for model in result.get("models", [])]
            
        except Exception as e:
            self.logger.error(f"Failed to list models: {e}")
            return []