from fastapi import APIRouter, HTTPException
import logging

from models.requests import GenerateTextRequest, ChatRequest, RAGRequest
from models.responses import GenerateTextResponse, ChatResponse, RAGResponse, ErrorResponse
from services.ai_processor import ai_processor

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/generate", response_model=GenerateTextResponse)
async def generate_text(request: GenerateTextRequest):
    """
    Text generation endpoint using Ollama
    
    Generates AI response from text input without audio processing.
    Uses the same Ollama service as the audio pipeline.
    """
    try:
        logger.info("Processing text generation request...")
        
        result = await ai_processor.generate_text(
            text=request.text,
            config=request.config.dict()
        )
        
        logger.info(f"Text generation completed in {result['processing_time']:.2f}s")
        
        return GenerateTextResponse(
            text=result["text"],
            tools=result.get("tools", []),
            processing_time=result["processing_time"]
        )
        
    except Exception as e:
        logger.error(f"Text generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="GenerationError",
                message="Text generation failed",
                details={"error": str(e)}
            ).dict()
        )

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint using Langchain
    
    Provides conversational AI capabilities with context management.
    """
    try:
        logger.info("Processing chat request...")
        
        result = await ai_processor.chat_with_langchain(
            message=request.message,
            conversation_history=request.conversation_history,
            config=request.config
        )
        
        logger.info(f"Chat completed in {result['processing_time']:.2f}s")
        
        return ChatResponse(
            text=result["text"],
            conversation_id=result.get("conversation_id"),
            processing_time=result["processing_time"]
        )
        
    except Exception as e:
        logger.error(f"Chat failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="ChatError",
                message="Chat processing failed",
                details={"error": str(e)}
            ).dict()
        )

@router.post("/rag", response_model=RAGResponse)
async def rag_query(request: RAGRequest):
    """
    RAG (Retrieval-Augmented Generation) endpoint using Langchain
    
    Performs knowledge base queries with context-aware responses.
    """
    try:
        logger.info(f"Processing RAG query: {request.query[:100]}...")
        
        result = await ai_processor.rag_query(
            query=request.query,
            knowledge_base=request.knowledge_base,
            config=request.config
        )
        
        logger.info(f"RAG query completed in {result['processing_time']:.2f}s")
        
        return RAGResponse(
            text=result["text"],
            sources=result.get("sources", []),
            processing_time=result["processing_time"]
        )
        
    except Exception as e:
        logger.error(f"RAG query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="RAGError",
                message="RAG query failed",
                details={"error": str(e)}
            ).dict()
        )