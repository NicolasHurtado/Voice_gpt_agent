"""
Base service classes and interfaces.
Provides common functionality and dependency injection patterns.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from ..core.logging import LoggerMixin
from ..core.exceptions import VoiceAgentException


class BaseService(LoggerMixin, ABC):
    """Base class for all services with common functionality."""
    
    def __init__(self, **dependencies):
        """Initialize service with dependencies."""
        self._dependencies = dependencies
        self.logger.info("Service initialized", service=self.__class__.__name__)
    
    def get_dependency(self, name: str) -> Any:
        """Get a dependency by name."""
        dependency = self._dependencies.get(name)
        if dependency is None:
            raise VoiceAgentException(
                f"Dependency '{name}' not found in {self.__class__.__name__}",
                error_code="DEPENDENCY_NOT_FOUND"
            )
        return dependency
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check for this service."""
        return {
            "service": self.__class__.__name__,
            "status": "healthy",
            "dependencies": list(self._dependencies.keys())
        }


class AudioProcessorInterface(ABC):
    """Interface for audio processing services."""
    
    @abstractmethod
    async def validate_audio(self, audio_data: bytes, format: str) -> bool:
        """Validate audio data and format."""
        pass
    
    @abstractmethod
    async def convert_audio_format(
        self, 
        audio_data: bytes, 
        source_format: str, 
        target_format: str
    ) -> bytes:
        """Convert audio from one format to another."""
        pass


class SpeechToTextInterface(ABC):
    """Interface for speech-to-text services."""
    
    @abstractmethod
    async def transcribe_audio(
        self, 
        audio_data: bytes, 
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """Transcribe audio to text."""
        pass


class TextToSpeechInterface(ABC):
    """Interface for text-to-speech services."""
    
    @abstractmethod
    async def synthesize_speech(
        self, 
        text: str, 
        voice: Optional[str] = None,
        language: Optional[str] = None
    ) -> bytes:
        """Convert text to speech audio."""
        pass


class ChatServiceInterface(ABC):
    """Interface for chat/conversation services."""
    
    @abstractmethod
    async def generate_response(
        self, 
        message: str, 
        session_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a response to a user message."""
        pass


class SessionManagerInterface(ABC):
    """Interface for session management services."""
    
    @abstractmethod
    async def create_session(self) -> str:
        """Create a new conversation session."""
        pass
    
    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information."""
        pass
    
    @abstractmethod
    async def update_session(
        self, 
        session_id: str, 
        data: Dict[str, Any]
    ) -> None:
        """Update session data."""
        pass
    
    @abstractmethod
    async def delete_session(self, session_id: str) -> None:
        """Delete a session."""
        pass
