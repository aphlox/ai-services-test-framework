import sys
import os
from pathlib import Path
import time
import base64
import logging
import asyncio
from typing import Dict, Any, Optional

# Add parent directory to path for importing existing services
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from whisper_service import WhisperService
from ollama_service import OllamaService
from langchain_service import LangchainService

logger = logging.getLogger(__name__)

class AIProcessor:
    """Main AI processing pipeline that coordinates Whisper, Ollama, and Langchain services"""
    
    def __init__(self):
        self.whisper_service = None
        self.ollama_service = None
        self.langchain_service = None
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize AI services"""
        try:
            # Initialize Whisper with GPU if available
            self.whisper_service = WhisperService(model_size="base")
            logger.info(f"Whisper service initialized on device: {self.whisper_service.device}")
            
            # Initialize Ollama
            self.ollama_service = OllamaService(host="http://localhost:11434", model="phi4")
            logger.info("Ollama service initialized")
            
            # Initialize Langchain
            self.langchain_service = LangchainService(host="http://localhost:11434", model="phi4")
            logger.info("Langchain service initialized")
            
        except Exception as e:
            logger.error(f"Error initializing AI services: {e}")
            raise
    
    async def process_audio_pipeline(self, audio_data: str, config: Dict[str, Any], audio_format: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Main audio processing pipeline: Audio → Whisper → Ollama → Response
        
        Args:
            audio_data: Base64 encoded audio data
            config: AI configuration (system_prompt, model, temperature, etc.)
            audio_format: Optional audio format specification
            
        Returns:
            Dict with text, userText, tools, and processing_time
        """
        start_time = time.time()
        
        try:
            # Import audio handler here to avoid circular imports
            from .audio_handler import AudioHandler
            
            # Step 1: Process and validate audio data
            audio_bytes = AudioHandler.process_audio_data(audio_data, audio_format)
            temp_audio_path = f"/tmp/audio_{int(time.time())}.wav"
            
            with open(temp_audio_path, 'wb') as f:
                f.write(audio_bytes)
            
            # Step 2: Transcribe with Whisper
            logger.info("Starting Whisper transcription...")
            whisper_start = time.time()
            transcription_result = self.whisper_service.transcribe(temp_audio_path)
            whisper_time = time.time() - whisper_start
            
            user_text = transcription_result.get("text", "").strip()
            logger.info(f"Whisper transcription completed in {whisper_time:.2f}s: '{user_text[:100]}...'")
            
            if not user_text:
                return {
                    "text": "I didn't catch that. Could you please repeat?",
                    "userText": "",
                    "tools": [],
                    "processing_time": time.time() - start_time
                }
            
            # Step 3: Generate response with Ollama
            logger.info("Starting Ollama generation...")
            ollama_start = time.time()
            
            # Create prompt with system prompt and user input
            system_prompt = config.get("system_prompt", "You are a helpful AI assistant.")
            full_prompt = f"{system_prompt}\n\nUser: {user_text}\nAssistant:"
            
            response = self.ollama_service.simple_generate(full_prompt)
            ollama_time = time.time() - ollama_start
            
            logger.info(f"Ollama generation completed in {ollama_time:.2f}s")
            
            # Clean up temporary file
            try:
                os.remove(temp_audio_path)
            except:
                pass
            
            total_time = time.time() - start_time
            
            return {
                "text": response,
                "userText": user_text,
                "tools": [],  # Tool integration to be implemented
                "processing_time": total_time,
                "gpu_usage": {
                    "whisper_time": whisper_time,
                    "ollama_time": ollama_time
                }
            }
            
        except Exception as e:
            logger.error(f"Error in audio processing pipeline: {e}")
            # Clean up temporary file on error
            try:
                if 'temp_audio_path' in locals():
                    os.remove(temp_audio_path)
            except:
                pass
            raise
    
    async def transcribe_audio(self, audio_data: str) -> Dict[str, Any]:
        """Transcribe audio using Whisper only"""
        start_time = time.time()
        
        try:
            # Decode and save audio
            audio_bytes = base64.b64decode(audio_data)
            temp_audio_path = f"/tmp/audio_{int(time.time())}.wav"
            
            with open(temp_audio_path, 'wb') as f:
                f.write(audio_bytes)
            
            # Transcribe
            result = self.whisper_service.transcribe(temp_audio_path)
            
            # Clean up
            try:
                os.remove(temp_audio_path)
            except:
                pass
            
            return {
                "text": result.get("text", ""),
                "language": result.get("language", "unknown"),
                "confidence": result.get("language_probability", None),
                "processing_time": time.time() - start_time
            }
            
        except Exception as e:
            logger.error(f"Error in transcription: {e}")
            try:
                if 'temp_audio_path' in locals():
                    os.remove(temp_audio_path)
            except:
                pass
            raise
    
    async def generate_text(self, text: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate text response using Ollama"""
        start_time = time.time()
        
        try:
            system_prompt = config.get("system_prompt", "You are a helpful AI assistant.")
            full_prompt = f"{system_prompt}\n\nUser: {text}\nAssistant:"
            
            response = self.ollama_service.simple_generate(full_prompt)
            
            return {
                "text": response,
                "tools": [],
                "processing_time": time.time() - start_time
            }
            
        except Exception as e:
            logger.error(f"Error in text generation: {e}")
            raise
    
    async def chat_with_langchain(self, message: str, conversation_history: list = None, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Chat using Langchain service"""
        start_time = time.time()
        
        try:
            response = self.langchain_service.simple_chat(message)
            
            return {
                "text": response,
                "conversation_id": None,  # To be implemented
                "processing_time": time.time() - start_time
            }
            
        except Exception as e:
            logger.error(f"Error in Langchain chat: {e}")
            raise
    
    async def rag_query(self, query: str, knowledge_base: str = "default", config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Perform RAG query using Langchain"""
        start_time = time.time()
        
        try:
            # This will need to be implemented based on available RAG methods
            response = self.langchain_service.simple_chat(f"Query: {query}")
            
            return {
                "text": response,
                "sources": [],  # To be implemented
                "processing_time": time.time() - start_time
            }
            
        except Exception as e:
            logger.error(f"Error in RAG query: {e}")
            raise
    
    def get_service_status(self) -> Dict[str, bool]:
        """Check status of all AI services"""
        status = {
            "whisper": False,
            "ollama": False,
            "langchain": False
        }
        
        try:
            # Test Whisper
            if self.whisper_service and hasattr(self.whisper_service, 'device'):
                status["whisper"] = True
        except:
            pass
        
        try:
            # Test Ollama - could implement a simple health check
            if self.ollama_service:
                status["ollama"] = True
        except:
            pass
        
        try:
            # Test Langchain
            if self.langchain_service:
                status["langchain"] = True
        except:
            pass
        
        return status

# Global AI processor instance
ai_processor = AIProcessor()