from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class AudioFormat(BaseModel):
    sampleRate: int = Field(default=48000, description="Audio sample rate in Hz")
    channels: int = Field(default=1, description="Number of audio channels")
    bitsPerSample: int = Field(default=16, description="Bits per audio sample")

class AIConfig(BaseModel):
    system_prompt: str = Field(description="System prompt for AI assistant")
    model: str = Field(default="phi4", description="AI model to use")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="AI generation temperature")
    max_tokens: int = Field(default=2048, gt=0, description="Maximum output tokens")

class ProcessAudioRequest(BaseModel):
    audio: str = Field(description="Base64 encoded WAV audio data")
    format: Optional[AudioFormat] = Field(default=None, description="Audio format specification")
    config: AIConfig = Field(description="AI configuration")

class GenerateTextRequest(BaseModel):
    text: str = Field(description="Input text to process")
    config: AIConfig = Field(description="AI configuration")
    
class TranscribeRequest(BaseModel):
    audio: str = Field(description="Base64 encoded audio data")
    format: Optional[AudioFormat] = Field(default=None, description="Audio format specification")

class ChatRequest(BaseModel):
    message: str = Field(description="User message")
    conversation_history: Optional[list] = Field(default=[], description="Previous conversation")
    config: Optional[Dict[str, Any]] = Field(default={}, description="Chat configuration")

class RAGRequest(BaseModel):
    query: str = Field(description="Query for RAG search")
    knowledge_base: Optional[str] = Field(default="default", description="Knowledge base to search")
    config: Optional[Dict[str, Any]] = Field(default={}, description="RAG configuration")