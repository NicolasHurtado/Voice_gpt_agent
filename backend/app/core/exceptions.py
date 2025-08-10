"""
Custom exception classes for the voice agent application.
Provides specific error types for different failure scenarios.
"""

from typing import Any, Dict, Optional


class VoiceAgentException(Exception):
    """Base exception class for all voice agent errors."""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class AudioProcessingError(VoiceAgentException):
    """Raised when audio processing fails."""
    pass


class SpeechToTextError(VoiceAgentException):
    """Raised when speech-to-text conversion fails."""
    pass


class TextToSpeechError(VoiceAgentException):
    """Raised when text-to-speech conversion fails."""
    pass


class GPTServiceError(VoiceAgentException):
    """Raised when GPT service interaction fails."""
    pass


class SessionError(VoiceAgentException):
    """Raised when session management fails."""
    pass


class ConfigurationError(VoiceAgentException):
    """Raised when application configuration is invalid."""
    pass


class ValidationError(VoiceAgentException):
    """Raised when input validation fails."""
    pass


class RateLimitError(VoiceAgentException):
    """Raised when API rate limits are exceeded."""
    pass
