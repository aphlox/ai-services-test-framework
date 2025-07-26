from fastapi import APIRouter
import logging
import time
import torch

from models.responses import HealthResponse, ServiceStatus, GPUMetrics
from services.ai_processor import ai_processor

router = APIRouter()
logger = logging.getLogger(__name__)

# Store startup time for uptime calculation
startup_time = time.time()

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint with comprehensive service and GPU status
    
    Returns:
    - Overall service health
    - Individual AI service status (Whisper, Ollama, Langchain)
    - GPU metrics and availability
    - System uptime
    """
    try:
        # Check individual service status
        service_status = ai_processor.get_service_status()
        
        # Determine overall status
        if all(service_status.values()):
            overall_status = "healthy"
        elif any(service_status.values()):
            overall_status = "degraded"
        else:
            overall_status = "error"
        
        # Get GPU metrics
        gpu_metrics = get_gpu_metrics()
        
        # Calculate uptime
        uptime = time.time() - startup_time
        
        return HealthResponse(
            status=overall_status,
            services=ServiceStatus(
                status=overall_status,
                whisper=service_status["whisper"],
                ollama=service_status["ollama"],
                langchain=service_status["langchain"]
            ),
            gpu=gpu_metrics,
            uptime=uptime,
            version="1.0.0"
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}", exc_info=True)
        
        # Return error status but don't fail the endpoint
        return HealthResponse(
            status="error",
            services=ServiceStatus(
                status="error",
                whisper=False,
                ollama=False,
                langchain=False
            ),
            gpu=GPUMetrics(gpu_available=False),
            uptime=time.time() - startup_time,
            version="1.0.0"
        )

def get_gpu_metrics() -> GPUMetrics:
    """Get current GPU metrics"""
    try:
        if torch.cuda.is_available():
            device_count = torch.cuda.device_count()
            if device_count > 0:
                # Get metrics for first GPU
                gpu_name = torch.cuda.get_device_name(0)
                
                # Get memory info
                memory_reserved = torch.cuda.memory_reserved(0) / 1e9  # Convert to GB
                memory_allocated = torch.cuda.memory_allocated(0) / 1e9
                
                # Get total memory (approximate)
                torch.cuda.empty_cache()  # Clear cache to get accurate reading
                total_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
                
                return GPUMetrics(
                    gpu_available=True,
                    gpu_name=gpu_name,
                    memory_used=memory_allocated,
                    memory_total=total_memory,
                    utilization=None  # PyTorch doesn't provide utilization directly
                )
        
        return GPUMetrics(gpu_available=False)
        
    except Exception as e:
        logger.warning(f"Failed to get GPU metrics: {e}")
        return GPUMetrics(gpu_available=False)

@router.get("/health/gpu")
async def gpu_status():
    """Detailed GPU status endpoint"""
    try:
        gpu_metrics = get_gpu_metrics()
        
        # Additional GPU information
        extra_info = {}
        if torch.cuda.is_available():
            extra_info.update({
                "cuda_version": torch.version.cuda,
                "pytorch_version": torch.__version__,
                "device_count": torch.cuda.device_count(),
                "current_device": torch.cuda.current_device() if torch.cuda.device_count() > 0 else None
            })
        
        return {
            "gpu_metrics": gpu_metrics.dict(),
            "additional_info": extra_info
        }
        
    except Exception as e:
        logger.error(f"GPU status check failed: {e}")
        return {"error": str(e)}

@router.get("/health/services")
async def services_status():
    """Detailed services status endpoint"""
    try:
        service_status = ai_processor.get_service_status()
        
        # Additional service information
        service_info = {
            "whisper": {
                "available": service_status["whisper"],
                "device": getattr(ai_processor.whisper_service, 'device', 'unknown') if ai_processor.whisper_service else 'not_initialized'
            },
            "ollama": {
                "available": service_status["ollama"],
                "host": getattr(ai_processor.ollama_service, 'host', 'unknown') if ai_processor.ollama_service else 'not_initialized',
                "model": getattr(ai_processor.ollama_service, 'model', 'unknown') if ai_processor.ollama_service else 'not_initialized'
            },
            "langchain": {
                "available": service_status["langchain"],
                "host": getattr(ai_processor.langchain_service, 'host', 'unknown') if ai_processor.langchain_service else 'not_initialized'
            }
        }
        
        return {
            "services": service_info,
            "overall_status": "healthy" if all(service_status.values()) else "degraded"
        }
        
    except Exception as e:
        logger.error(f"Services status check failed: {e}")
        return {"error": str(e)}