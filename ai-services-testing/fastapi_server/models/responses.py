from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ToolUsage(BaseModel):
    name: str = Field(description="Tool name that was used")
    success: bool = Field(description="Whether tool execution was successful")
    result: Optional[str] = Field(default=None, description="Tool execution result")

class ProcessAudioResponse(BaseModel):
    text: str = Field(description="AI assistant response text")
    userText: str = Field(description="Transcribed user speech")
    tools: List[ToolUsage] = Field(default=[], description="Tools that were executed")
    processing_time: float = Field(description="Total processing time in seconds")
    gpu_usage: Optional[Dict[str, float]] = Field(default=None, description="GPU usage metrics")

class GenerateTextResponse(BaseModel):
    text: str = Field(description="Generated text response")
    tools: List[ToolUsage] = Field(default=[], description="Tools that were executed")
    processing_time: float = Field(description="Processing time in seconds")

class TranscribeResponse(BaseModel):
    text: str = Field(description="Transcribed text")
    language: str = Field(description="Detected language")
    confidence: Optional[float] = Field(default=None, description="Transcription confidence")
    processing_time: float = Field(description="Processing time in seconds")

class ChatResponse(BaseModel):
    text: str = Field(description="Chat response")
    conversation_id: Optional[str] = Field(default=None, description="Conversation identifier")
    processing_time: float = Field(description="Processing time in seconds")

class RAGResponse(BaseModel):
    text: str = Field(description="RAG response")
    sources: List[Dict[str, Any]] = Field(default=[], description="Source documents used")
    processing_time: float = Field(description="Processing time in seconds")

class GPUMetrics(BaseModel):
    gpu_available: bool = Field(description="Whether GPU is available")
    gpu_name: Optional[str] = Field(default=None, description="GPU device name")
    memory_used: Optional[float] = Field(default=None, description="GPU memory used (GB)")
    memory_total: Optional[float] = Field(default=None, description="Total GPU memory (GB)")
    utilization: Optional[float] = Field(default=None, description="GPU utilization percentage")

class ServiceStatus(BaseModel):
    status: str = Field(description="Service status (healthy/degraded/error)")
    whisper: bool = Field(description="Whisper service availability")
    ollama: bool = Field(description="Ollama service availability")
    langchain: bool = Field(description="Langchain service availability")

class HealthResponse(BaseModel):
    status: str = Field(description="Overall health status")
    services: ServiceStatus = Field(description="Individual service statuses")
    gpu: GPUMetrics = Field(description="GPU metrics")
    uptime: float = Field(description="Server uptime in seconds")
    version: str = Field(description="API version")

class ErrorResponse(BaseModel):
    error: str = Field(description="Error type")
    message: str = Field(description="Error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")