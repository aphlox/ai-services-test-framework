#!/usr/bin/env python3
"""
Final validation script for AI Services Testing Framework
"""

import sys
import os
import time
import tempfile
import numpy as np

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from whisper_service import WhisperService
from ollama_service import OllamaService

def create_test_audio():
    """Create a simple test audio file"""
    try:
        import scipy.io.wavfile as wavfile
        
        sample_rate = 16000
        duration = 2  # seconds
        frequency = 440  # Hz
        
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = np.sin(2 * np.pi * frequency * t)
        audio_data = (audio_data * 32767).astype(np.int16)
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            wavfile.write(f.name, sample_rate, audio_data)
            return f.name
    except ImportError:
        print("Warning: scipy not available, using dummy audio")
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            f.write(b'dummy audio data')
            return f.name

def test_whisper_service():
    """Test Whisper service functionality"""
    print("🎤 Testing Whisper Service...")
    
    try:
        service = WhisperService(model_size="base", device="cpu")
        print(f"✅ WhisperService initialized (model: {service.model_size}, device: {service.device})")
        
        # Test available models
        models = service.get_available_models()
        print(f"✅ Available models: {len(models)} models found")
        
        # Test with actual audio (will use real Whisper model)
        print("⏳ Testing audio transcription (this may take a moment)...")
        audio_file = create_test_audio()
        
        try:
            start_time = time.time()
            result = service.transcribe(audio_file)
            duration = time.time() - start_time
            
            print(f"✅ Transcription completed in {duration:.2f}s")
            print(f"   Text: '{result['text']}'")
            print(f"   Language: {result['language']} (confidence: {result['language_probability']:.2f})")
            print(f"   Duration: {result['duration']:.2f}s")
            print(f"   Word count: {result['word_count']}")
            
            assert True
            
        except Exception as e:
            print(f"❌ Transcription failed: {e}")
            assert False, f"Transcription failed: {e}"
            
        finally:
            # Cleanup
            try:
                os.unlink(audio_file)
            except:
                pass
                
    except Exception as e:
        print(f"❌ WhisperService initialization failed: {e}")
        assert False, f"WhisperService initialization failed: {e}"

def test_ollama_service():
    """Test Ollama service connectivity"""
    print("\n🤖 Testing Ollama Service...")
    
    try:
        service = OllamaService()
        print(f"✅ OllamaService initialized (host: {service.host}, model: {service.model})")
        
        # Test health check
        is_healthy = service.health_check()
        if is_healthy:
            print("✅ Ollama service is healthy and responding")
            
            # Try to list models
            models = service.list_models()
            print(f"✅ Available models: {models}")
            
            # Try simple generation
            try:
                response = service.simple_generate("Hello, can you respond?")
                print(f"✅ Simple generation successful: '{response[:50]}...'")
            except Exception as e:
                print(f"⚠️  Simple generation failed: {e}")
                
            assert True
        else:
            print("⚠️  Ollama service is not responding (expected if container not started)")
            assert False, "Ollama service is not responding"
            
    except Exception as e:
        print(f"❌ OllamaService initialization failed: {e}")
        assert False, f"OllamaService initialization failed: {e}"

def run_performance_test():
    """Run basic performance validation"""
    print("\n⚡ Performance Validation...")
    
    # Test memory usage
    try:
        import psutil
        process = psutil.Process()
        memory_mb = process.memory_info().rss / 1024 / 1024
        print(f"✅ Current memory usage: {memory_mb:.1f} MB")
        
        if memory_mb < 500:  # Less than 500MB is good
            print("✅ Memory usage is within acceptable limits")
        else:
            print("⚠️  Memory usage is high but may be acceptable")
            
    except ImportError:
        print("⚠️  psutil not available, skipping memory check")
    
    # Test import times
    start_time = time.time()
    try:
        import whisper
        whisper_import_time = time.time() - start_time
        print(f"✅ Whisper import time: {whisper_import_time:.2f}s")
    except Exception as e:
        print(f"❌ Whisper import failed: {e}")

def main():
    """Main validation function"""
    print("🚀 AI Services Testing Framework - Final Validation")
    print("=" * 60)
    
    results = []
    
    # Test Whisper
    whisper_ok = test_whisper_service()
    results.append(("Whisper Service", whisper_ok))
    
    # Test Ollama
    ollama_ok = test_ollama_service()
    results.append(("Ollama Service", ollama_ok))
    
    # Performance tests
    run_performance_test()
    
    # Summary
    print("\n📊 Validation Summary")
    print("=" * 60)
    
    for service, status in results:
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {service}: {'PASS' if status else 'FAIL'}")
    
    passed = sum(1 for _, status in results if status)
    total = len(results)
    
    print(f"\n🏆 Overall: {passed}/{total} services validated successfully")
    
    if passed == total:
        print("🎉 All core services are working!")
    elif passed > 0:
        print("⚠️  Partial success - some services may need attention")
    else:
        print("❌ Critical issues found - services need troubleshooting")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)