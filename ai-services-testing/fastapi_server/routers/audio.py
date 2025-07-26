from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import logging
import time

from models.requests import ProcessAudioRequest, TranscribeRequest
from models.responses import ProcessAudioResponse, TranscribeResponse, ErrorResponse
from services.ai_processor import ai_processor

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/process-audio", response_model=ProcessAudioResponse)
async def process_audio(request: ProcessAudioRequest):
    """
    Main audio processing endpoint: Audio → Whisper → Ollama → Response
    
    This endpoint processes audio input through the complete AI pipeline:
    1. Receives base64 encoded audio
    2. Transcribes using Whisper (GPU accelerated)
    3. Generates response using Ollama (GPU accelerated)
    4. Returns wespoke-compatible response
    """
    try:
        logger.info("Processing audio request...")
        
        # Process through AI pipeline
        result = await ai_processor.process_audio_pipeline(
            audio_data=request.audio,
            config=request.config.dict(),
            audio_format=request.format.dict() if request.format else None
        )
        
        logger.info(f"Audio processing completed in {result['processing_time']:.2f}s")
        
        return ProcessAudioResponse(
            text=result["text"],
            userText=result["userText"],
            tools=result.get("tools", []),
            processing_time=result["processing_time"],
            gpu_usage=result.get("gpu_usage")
        )
        
    except ValueError as e:
        logger.warning(f"Invalid request: {e}")
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error="ValidationError",
                message=str(e)
            ).dict()
        )
    except Exception as e:
        logger.error(f"Audio processing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="ProcessingError",
                message="Audio processing failed",
                details={"error": str(e)}
            ).dict()
        )

@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(request: TranscribeRequest):
    """
    Whisper-only transcription endpoint
    
    Transcribes audio to text using Whisper without further processing.
    Useful for getting just the transcription without AI response generation.
    """
    try:
        logger.info("Processing transcription request...")
        
        # Transcribe using Whisper only
        result = await ai_processor.transcribe_audio(request.audio)
        
        logger.info(f"Transcription completed in {result['processing_time']:.2f}s")
        
        return TranscribeResponse(
            text=result["text"],
            language=result["language"],
            confidence=result.get("confidence"),
            processing_time=result["processing_time"]
        )
        
    except ValueError as e:
        logger.warning(f"Invalid transcription request: {e}")
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(
                error="ValidationError",
                message=str(e)
            ).dict()
        )
    except Exception as e:
        logger.error(f"Transcription failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="TranscriptionError",
                message="Audio transcription failed",
                details={"error": str(e)}
            ).dict()
        )