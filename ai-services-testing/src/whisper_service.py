import whisper
from typing import Dict, Any, List
import logging
import time

class WhisperService:
    def __init__(self, model_size: str = "base", device: str = "cpu"):
        self.model_size = model_size
        self.device = device
        self.model = None
        self.logger = logging.getLogger(__name__)
        
    def _load_model(self):
        """Lazy loading of the model"""
        if self.model is None:
            self.logger.info(f"Loading Whisper model: {self.model_size}")
            self.model = whisper.load_model(self.model_size, device=self.device)
            
    def transcribe(self, audio_path: str) -> Dict[str, Any]:
        """
        Transcribe audio file to text
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dict containing transcription results
        """
        try:
            start_time = time.time()
            self._load_model()
            
            # Transcribe audio
            result = self.model.transcribe(audio_path)
            
            # Calculate word count
            word_count = len(result["text"].split()) if result["text"] else 0
            
            processing_time = time.time() - start_time
            
            return {
                "text": result["text"].strip(),
                "language": result["language"],
                "language_probability": result.get("language_probability", 0.0),
                "duration": result.get("duration", 0.0),
                "word_count": word_count,
                "processing_time": processing_time
            }
            
        except Exception as e:
            self.logger.error(f"Transcription failed: {e}")
            raise
    
    def get_available_models(self) -> List[str]:
        """Get list of available Whisper models"""
        return ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"]