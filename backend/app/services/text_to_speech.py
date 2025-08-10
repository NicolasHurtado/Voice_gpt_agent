"""
Text-to-speech service using OpenAI TTS API.
Provides high-quality speech synthesis with multiple voice options.
"""

import tempfile
from typing import Optional, Dict, Any
from pathlib import Path

import httpx
from openai import AsyncOpenAI

from .base import BaseService, TextToSpeechInterface
from ..core.exceptions import TextToSpeechError, RateLimitError
from ..core.config import settings


class TextToSpeechService(BaseService, TextToSpeechInterface):
    """Service for converting text to speech using OpenAI TTS."""
    
    def __init__(self):
        super().__init__()
        # Validate API key
        if not settings.openai_api_key or settings.openai_api_key == "sk-placeholder-key":
            self.logger.warning(
                "OpenAI API key not properly configured for TTS. "
                "Using placeholder key - TTS requests will fail."
            )
        
        # Use real OpenAI API for TTS since Ollama doesn't support TTS
        self.client = AsyncOpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
        self.openai_settings = settings.openai_settings
        self.available_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        
        self.logger.info(
            "TTS service initialized",
            tts_model=self.openai_settings.tts_model,
            default_voice=self.openai_settings.tts_voice
        )
    
    async def synthesize_speech(
        self, 
        text: str, 
        voice: Optional[str] = None,
        language: Optional[str] = None
    ) -> bytes:
        """
        Convert text to speech using OpenAI TTS.
        
        Args:
            text: Text to convert to speech
            voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
            language: Language code (currently not used by OpenAI TTS)
            
        Returns:
            Audio bytes in MP3 format
            
        Raises:
            TextToSpeechError: If synthesis fails
        """
        try:
            # Validate and set voice
            voice = voice or self.openai_settings.tts_voice

            if voice not in self.available_voices:
                self.logger.warning(
                    f"Invalid voice '{voice}', using default '{self.openai_settings.tts_voice}'"
                )
                voice = self.openai_settings.tts_voice

            self.logger.info(f"Using voice: {voice}")

            # Validate text length
            if len(text) > 4096:
                raise TextToSpeechError(
                    "Text too long for TTS (max 4096 characters)",
                    error_code="TEXT_TOO_LONG"
                )
            
            if not text.strip():
                raise TextToSpeechError(
                    "Empty text provided for TTS",
                    error_code="EMPTY_TEXT"
                )
            
            # Preprocess text for better speech synthesis
            processed_text = self._preprocess_text(text)
            self.logger.info(f"Processed text: {processed_text}")
            
            # Generate speech
            response = await self.client.audio.speech.with_streaming_response.create(
                model=self.openai_settings.tts_model,
                voice=voice,
                input=processed_text,
                response_format="mp3",
                speed=1.0
            )
            self.logger.info(f"Response: {response}")
            # Get audio data
            audio_data = response.content
            
            self.logger.info(
                "Text-to-speech synthesis completed",
                text_length=len(text),
                voice=voice,
                audio_size=len(audio_data)
            )
            
            return audio_data
            
        except httpx.HTTPStatusError as e:
            self.logger.error(
                "HTTP error in TTS request",
                status_code=e.response.status_code,
                response_text=e.response.text,
                url=str(e.request.url) if e.request else "Unknown"
            )
            if e.response.status_code == 429:
                raise RateLimitError(
                    "OpenAI API rate limit exceeded",
                    error_code="RATE_LIMIT_EXCEEDED"
                )
            else:
                raise TextToSpeechError(
                    f"OpenAI API error: {e.response.status_code} - {e.response.text}",
                    error_code="API_ERROR"
                )
        except Exception as e:
            self.logger.error("Text-to-speech synthesis failed", error=str(e))
            raise TextToSpeechError(
                f"Speech synthesis failed: {str(e)}",
                error_code="SYNTHESIS_ERROR"
            )
    
    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text for better speech synthesis.
        
        Args:
            text: Raw text
            
        Returns:
            Processed text optimized for TTS
        """
        # Remove excessive whitespace
        processed = " ".join(text.split())
        
        # Add pauses for better speech flow
        processed = processed.replace(".", ". ")
        processed = processed.replace("!", "! ")
        processed = processed.replace("?", "? ")
        processed = processed.replace(",", ", ")
        processed = processed.replace(";", "; ")
        processed = processed.replace(":", ": ")
        
        # Handle common abbreviations for better pronunciation
        abbreviations = {
            "AI": "A.I.",
            "API": "A.P.I.",
            "URL": "U.R.L.",
            "HTTP": "H.T.T.P.",
            "JSON": "J.S.O.N.",
            "XML": "X.M.L.",
            "SQL": "S.Q.L.",
            "CPU": "C.P.U.",
            "GPU": "G.P.U.",
            "RAM": "R.A.M.",
        }
        
        for abbr, pronunciation in abbreviations.items():
            processed = processed.replace(f" {abbr} ", f" {pronunciation} ")
            processed = processed.replace(f" {abbr}.", f" {pronunciation}.")
            processed = processed.replace(f" {abbr},", f" {pronunciation},")
        
        # Clean up extra spaces
        processed = " ".join(processed.split())
        
        return processed
    
    async def get_available_voices(self) -> list:
        """
        Get list of available voices.
        
        Returns:
            List of available voice names
        """
        return self.available_voices.copy()
    
    async def synthesize_with_options(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: float = 1.0,
        format: str = "mp3"
    ) -> bytes:
        """
        Advanced speech synthesis with additional options.
        
        Args:
            text: Text to convert
            voice: Voice to use
            speed: Speech speed (0.25 to 4.0)
            format: Audio format (mp3, opus, aac, flac)
            
        Returns:
            Audio bytes in specified format
        """
        try:
            # Validate speed
            speed = max(0.25, min(4.0, speed))
            
            # Validate format
            supported_formats = ["mp3", "opus", "aac", "flac"]
            if format not in supported_formats:
                format = "mp3"
            
            voice = voice or self.openai_settings.tts_voice
            processed_text = self._preprocess_text(text)
            
            response = await self.client.audio.speech.create(
                model=self.openai_settings.tts_model,
                voice=voice,
                input=processed_text,
                response_format=format,
                speed=speed
            )
            
            audio_data = response.content
            
            self.logger.info(
                "Advanced TTS synthesis completed",
                text_length=len(text),
                voice=voice,
                speed=speed,
                format=format,
                audio_size=len(audio_data)
            )
            
            return audio_data
            
        except Exception as e:
            self.logger.error("Advanced TTS synthesis failed", error=str(e))
            raise TextToSpeechError(
                f"Advanced synthesis failed: {str(e)}",
                error_code="ADVANCED_SYNTHESIS_ERROR"
            )
    
    async def save_audio_to_file(
        self, 
        audio_data: bytes, 
        file_path: Optional[str] = None
    ) -> str:
        """
        Save audio data to a file.
        
        Args:
            audio_data: Audio bytes
            file_path: Optional file path, if None creates temp file
            
        Returns:
            Path to saved file
        """
        try:
            if file_path is None:
                # Create temporary file
                temp_file = tempfile.NamedTemporaryFile(
                    suffix=".mp3", 
                    delete=False
                )
                file_path = temp_file.name
                temp_file.close()
            
            # Write audio data to file
            with open(file_path, "wb") as f:
                f.write(audio_data)
            
            self.logger.info(
                "Audio saved to file",
                file_path=file_path,
                size=len(audio_data)
            )
            
            return file_path
            
        except Exception as e:
            self.logger.error("Failed to save audio file", error=str(e))
            raise TextToSpeechError(
                f"Failed to save audio: {str(e)}",
                error_code="FILE_SAVE_ERROR"
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the text-to-speech service."""
        base_health = await super().health_check()
        
        try:
            # Test with a simple phrase
            test_text = "Hello, this is a test."
            audio_data = await self.synthesize_speech(test_text)
            
            base_health.update({
                "tts_model": self.openai_settings.tts_model,
                "available_voices": self.available_voices,
                "test_synthesis_size": len(audio_data),
                "status": "healthy"
            })
            
        except Exception as e:
            base_health.update({
                "status": "unhealthy",
                "error": str(e)
            })
        
        return base_health
