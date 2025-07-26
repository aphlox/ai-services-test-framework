import sys
import os
from pathlib import Path

# Add the parent directory to Python path to import existing services
sys.path.append(str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import logging
import time
from datetime import datetime

from routers import audio, text, health
from models.responses import ErrorResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="AI Services API",
    description="FastAPI backend for Whisper, Ollama, and Langchain integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware - similar to wespoke configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Store startup time for health checks
startup_time = time.time()

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("AI Services API starting up...")
    logger.info("Checking AI services availability...")
    
    # Initialize services here if needed
    # This will be implemented in the services module
    
    logger.info("AI Services API startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("AI Services API shutting down...")

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="InternalServerError",
            message="An unexpected error occurred",
            details={"type": type(exc).__name__}
        ).dict()
    )

# Include routers
app.include_router(audio.router, prefix="/ai", tags=["audio"])
app.include_router(text.router, prefix="/ai", tags=["text"]) 
app.include_router(health.router, prefix="/ai", tags=["health"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "AI Services API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }

@app.get("/ai")
async def ai_info():
    """AI services information"""
    return {
        "services": ["whisper", "ollama", "langchain"],
        "endpoints": [
            "/ai/process-audio",
            "/ai/transcribe", 
            "/ai/generate",
            "/ai/chat",
            "/ai/rag",
            "/ai/health"
        ],
        "uptime": time.time() - startup_time
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )