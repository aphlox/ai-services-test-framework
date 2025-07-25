from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class TranscriptionResponse(BaseModel):
    text: str
    language: str
    language_probability: float
    duration: float
    word_count: int

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

class StructuredRequest(BaseModel):
    prompt: str
    response_schema: Dict[str, Any]
    model: Optional[str] = "phi3"
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 2048

class FunctionCallRequest(BaseModel):
    prompt: str
    tools: List[Dict[str, Any]]
    model: Optional[str] = "phi3"
    temperature: Optional[float] = 0.7