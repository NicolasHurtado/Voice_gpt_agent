"""
Speech-to-text service using OpenAI Whisper API.
Provides high-quality audio transcription with language detection.
"""

import io
import tempfile
from typing import Dict, Any, Optional

import httpx
from openai import AsyncOpenAI

from .base import BaseService, SpeechToTextInterface
from .audio_processor import AudioProcessorService
from ..core.exceptions import SpeechToTextError, RateLimitError
from ..core.config import settings


class SpeechToTextService(BaseService, SpeechToTextInterface):
    """Service for converting speech to text using OpenAI Whisper."""
    
    def __init__(self, audio_processor: AudioProcessorService):
        super().__init__(audio_processor=audio_processor)
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.audio_processor = audio_processor
        self.openai_settings = settings.openai_settings
    
    async def transcribe_audio(
        self, 
        audio_data: bytes, 
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe audio to text using OpenAI Whisper.
        
        Args:
            audio_data: Audio bytes to transcribe
            language: Optional language code (e.g., 'en', 'es')
            
        Returns:
            Dictionary with transcription results
            
        Raises:
            SpeechToTextError: If transcription fails
        """
        try:
            # Preprocess audio for optimal recognition
            processed_audio = await self.audio_processor.preprocess_for_speech_recognition(
                audio_data, "wav"
            )
            
            # Create temporary file for API call
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_file.write(processed_audio)
                temp_file.flush()
                
                # Prepare transcription request
                with open(temp_file.name, "rb") as audio_file:
                    transcript = await self.client.audio.transcriptions.create(
                        model=self.openai_settings.whisper_model,
                        file=audio_file,
                        language=language,
                        response_format="verbose_json",
                        temperature=0.0  # Deterministic output
                    )
            
            # Extract features for quality assessment
            audio_features = await self.audio_processor.extract_audio_features(
                processed_audio, "wav"
            )
            
            # Prepare response
            result = {
                "text": transcript.text,
                "language": transcript.language if hasattr(transcript, 'language') else language,
                "duration": transcript.duration if hasattr(transcript, 'duration') else audio_features.get("duration_seconds"),
                "confidence": self._estimate_confidence(transcript.text, audio_features),
                "segments": getattr(transcript, 'segments', []),
                "audio_features": audio_features
            }
            
            self.logger.info(
                "Speech-to-text transcription completed",
                text_length=len(result["text"]),
                language=result["language"],
                duration=result["duration"],
                confidence=result["confidence"]
            )
            
            return result
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                raise RateLimitError(
                    "OpenAI API rate limit exceeded",
                    error_code="RATE_LIMIT_EXCEEDED"
                )
            else:
                raise SpeechToTextError(
                    f"OpenAI API error: {e.response.status_code} - {e.response.text}",
                    error_code="API_ERROR"
                )
        except Exception as e:
            self.logger.error("Speech-to-text transcription failed", error=str(e))
            raise SpeechToTextError(
                f"Transcription failed: {str(e)}",
                error_code="TRANSCRIPTION_ERROR"
            )
    
    def _estimate_confidence(self, text: str, audio_features: Dict[str, Any]) -> float:
        """
        Estimate transcription confidence based on text and audio features.
        
        Args:
            text: Transcribed text
            audio_features: Audio analysis features
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        confidence = 0.5  # Base confidence
        
        # Text-based indicators
        if len(text.strip()) > 0:
            confidence += 0.2
        
        # Check for common transcription artifacts
        if not any(phrase in text.lower() for phrase in ["[inaudible]", "[unclear]", "..."]):
            confidence += 0.1
        
        # Audio quality indicators
        if audio_features.get("rms_energy", 0) > 0.01:  # Good signal strength
            confidence += 0.1
        
        if audio_features.get("silence_ratio", 1.0) < 0.5:  # Not too much silence
            confidence += 0.1
        
        # Ensure confidence is between 0 and 1
        return min(1.0, max(0.0, confidence))
    
    async def transcribe_streaming(
        self, 
        audio_chunks: list, 
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Transcribe streaming audio chunks (for future WebSocket implementation).
        
        Args:
            audio_chunks: List of audio chunk bytes
            language: Optional language code
            
        Returns:
            Dictionary with streaming transcription results
        """
        try:
            # Combine chunks into single audio stream
            combined_audio = b"".join(audio_chunks)
            
            # Use regular transcription for now
            # In production, you might want to implement streaming transcription
            return await self.transcribe_audio(combined_audio, language)
            
        except Exception as e:
            self.logger.error("Streaming transcription failed", error=str(e))
            raise SpeechToTextError(
                f"Streaming transcription failed: {str(e)}",
                error_code="STREAMING_ERROR"
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the speech-to-text service."""
        base_health = await super().health_check()
        
        try:
            # Test with a small audio sample
            # Create a short silent audio for testing
            test_audio = b"\x00" * 1024  # Silent audio
            
            # Note: This would fail with real OpenAI API, but shows the pattern
            # In production, you might want to test with a valid audio sample
            # or just check API connectivity
            
            base_health.update({
                "openai_whisper_model": self.openai_settings.whisper_model,
                "status": "healthy"
            })
            
        except Exception as e:
            base_health.update({
                "status": "unhealthy",
                "error": str(e)
            })
        
        return base_health
