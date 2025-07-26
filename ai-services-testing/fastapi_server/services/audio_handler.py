import io
import wave
import base64
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class AudioHandler:
    """Handles audio format processing and validation for the FastAPI server"""
    
    @staticmethod
    def create_wav_header(data_length: int, sample_rate: int = 48000, channels: int = 1, bits_per_sample: int = 16) -> bytes:
        """
        Create WAV header for PCM audio data
        
        Args:
            data_length: Length of audio data in bytes
            sample_rate: Audio sample rate (default: 48000 Hz)
            channels: Number of audio channels (default: 1 for mono)
            bits_per_sample: Bits per sample (default: 16)
            
        Returns:
            WAV header as bytes
        """
        # Calculate derived values
        byte_rate = sample_rate * channels * bits_per_sample // 8
        block_align = channels * bits_per_sample // 8
        
        # Create WAV header
        header = io.BytesIO()
        
        # RIFF header
        header.write(b'RIFF')
        header.write((data_length + 36).to_bytes(4, 'little'))  # File size - 8
        header.write(b'WAVE')
        
        # fmt chunk
        header.write(b'fmt ')
        header.write((16).to_bytes(4, 'little'))  # fmt chunk size
        header.write((1).to_bytes(2, 'little'))   # Audio format (PCM)
        header.write(channels.to_bytes(2, 'little'))
        header.write(sample_rate.to_bytes(4, 'little'))
        header.write(byte_rate.to_bytes(4, 'little'))
        header.write(block_align.to_bytes(2, 'little'))
        header.write(bits_per_sample.to_bytes(2, 'little'))
        
        # data chunk
        header.write(b'data')
        header.write(data_length.to_bytes(4, 'little'))
        
        return header.getvalue()
    
    @staticmethod
    def process_audio_data(audio_base64: str, audio_format: Optional[Dict[str, Any]] = None) -> bytes:
        """
        Process base64 audio data and ensure it's in WAV format
        
        Args:
            audio_base64: Base64 encoded audio data
            audio_format: Optional audio format specification
            
        Returns:
            WAV formatted audio data as bytes
        """
        try:
            # Decode base64 audio
            audio_bytes = base64.b64decode(audio_base64)
            
            # Check if it's already a WAV file (starts with RIFF header)
            if audio_bytes.startswith(b'RIFF') and b'WAVE' in audio_bytes[:20]:
                logger.info("Audio is already in WAV format")
                return audio_bytes
            
            # If not WAV, assume it's raw PCM data and add WAV header
            if audio_format:
                sample_rate = audio_format.get('sampleRate', 48000)
                channels = audio_format.get('channels', 1)
                bits_per_sample = audio_format.get('bitsPerSample', 16)
            else:
                # Default format (matching wespoke's default)
                sample_rate = 48000
                channels = 1
                bits_per_sample = 16
            
            logger.info(f"Adding WAV header - Rate: {sample_rate}Hz, Channels: {channels}, Bits: {bits_per_sample}")
            
            # Create WAV header and combine with PCM data
            wav_header = AudioHandler.create_wav_header(
                len(audio_bytes), sample_rate, channels, bits_per_sample
            )
            
            return wav_header + audio_bytes
            
        except Exception as e:
            logger.error(f"Error processing audio data: {e}")
            raise ValueError(f"Invalid audio data: {e}")
    
    @staticmethod
    def validate_audio_format(audio_format: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize audio format specification
        
        Args:
            audio_format: Audio format dictionary
            
        Returns:
            Validated and normalized audio format
        """
        validated = {
            'sampleRate': 48000,
            'channels': 1,
            'bitsPerSample': 16
        }
        
        if audio_format:
            # Validate sample rate
            sample_rate = audio_format.get('sampleRate', 48000)
            if sample_rate in [8000, 16000, 22050, 44100, 48000]:
                validated['sampleRate'] = sample_rate
            else:
                logger.warning(f"Unsupported sample rate {sample_rate}, using 48000")
            
            # Validate channels
            channels = audio_format.get('channels', 1)
            if channels in [1, 2]:
                validated['channels'] = channels
            else:
                logger.warning(f"Unsupported channel count {channels}, using 1")
            
            # Validate bits per sample
            bits_per_sample = audio_format.get('bitsPerSample', 16)
            if bits_per_sample in [8, 16, 24, 32]:
                validated['bitsPerSample'] = bits_per_sample
            else:
                logger.warning(f"Unsupported bits per sample {bits_per_sample}, using 16")
        
        return validated
    
    @staticmethod
    def get_audio_info(audio_bytes: bytes) -> Dict[str, Any]:
        """
        Extract information from WAV audio data
        
        Args:
            audio_bytes: WAV audio data
            
        Returns:
            Dictionary with audio information
        """
        try:
            # Create a BytesIO object to read like a file
            audio_io = io.BytesIO(audio_bytes)
            
            with wave.open(audio_io, 'rb') as wav_file:
                return {
                    'channels': wav_file.getnchannels(),
                    'sample_rate': wav_file.getframerate(),
                    'bits_per_sample': wav_file.getsampwidth() * 8,
                    'frames': wav_file.getnframes(),
                    'duration': wav_file.getnframes() / wav_file.getframerate()
                }
                
        except Exception as e:
            logger.warning(f"Could not extract audio info: {e}")
            return {
                'channels': 1,
                'sample_rate': 48000,
                'bits_per_sample': 16,
                'frames': 0,
                'duration': 0.0
            }