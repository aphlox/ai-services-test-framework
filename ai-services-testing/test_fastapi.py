#!/usr/bin/env python3
"""
Simple test script for FastAPI backend
"""

import sys
import os
import asyncio
import base64
import wave
import numpy as np
from pathlib import Path

# Add fastapi_server to path
sys.path.append(str(Path(__file__).parent / "fastapi_server"))

from services.ai_processor import AIProcessor
from services.audio_handler import AudioHandler

def create_test_audio():
    """Create a simple test audio file"""
    # Generate 3 seconds of sine wave at 16kHz
    sample_rate = 16000
    duration = 3
    frequency = 440  # A note
    
    t = np.linspace(0, duration, sample_rate * duration, False)
    audio_data = np.sin(2 * np.pi * frequency * t) * 0.3
    
    # Convert to 16-bit PCM
    audio_data = (audio_data * 32767).astype(np.int16)
    
    # Save as WAV file
    filename = "test_audio_fastapi.wav"
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 2 bytes = 16 bits
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_data.tobytes())
    
    return filename

async def test_ai_processor():
    """Test the AI processor directly"""
    print("🧪 Testing AI Processor...")
    
    # Create test audio
    audio_file = create_test_audio()
    print(f"✅ Created test audio: {audio_file}")
    
    # Read and encode audio
    with open(audio_file, 'rb') as f:
        audio_bytes = f.read()
    
    audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
    print(f"✅ Encoded audio: {len(audio_base64)} characters")
    
    try:
        # Test audio handler
        print("\n🔧 Testing Audio Handler...")
        processed_audio = AudioHandler.process_audio_data(audio_base64)
        print(f"✅ Audio processed: {len(processed_audio)} bytes")
        
        audio_info = AudioHandler.get_audio_info(processed_audio)
        print(f"✅ Audio info: {audio_info}")
        
        # Test AI processor
        print("\n🤖 Testing AI Processor...")
        ai_processor = AIProcessor()
        print("✅ AI Processor initialized")
        
        # Check service status
        status = ai_processor.get_service_status()
        print(f"✅ Service status: {status}")
        
        # Test audio pipeline
        config = {
            "system_prompt": "You are a helpful AI assistant.",
            "model": "phi4",
            "temperature": 0.7,
            "max_tokens": 100
        }
        
        print("\n🎯 Testing Audio Pipeline...")
        result = await ai_processor.process_audio_pipeline(audio_base64, config)
        
        print("✅ Audio Pipeline Results:")
        print(f"   User Text: '{result['userText']}'")
        print(f"   AI Response: '{result['text'][:100]}...'")
        print(f"   Processing Time: {result['processing_time']:.2f}s")
        print(f"   GPU Usage: {result.get('gpu_usage', {})}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        if os.path.exists(audio_file):
            os.remove(audio_file)
            print(f"🧹 Cleaned up {audio_file}")

def test_health():
    """Test health check functionality"""
    print("\n💚 Testing Health Check...")
    
    try:
        from routers.health import get_gpu_metrics
        
        gpu_metrics = get_gpu_metrics()
        print(f"✅ GPU Metrics: {gpu_metrics.dict()}")
        
    except Exception as e:
        print(f"❌ Health check error: {e}")

if __name__ == "__main__":
    print("🚀 FastAPI Backend Test Suite")
    print("=" * 50)
    
    # Test health first
    test_health()
    
    # Test AI processor
    asyncio.run(test_ai_processor())
    
    print("\n✅ Test suite completed!")