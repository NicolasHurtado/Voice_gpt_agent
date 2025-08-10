"""
Dependency injection container for managing service dependencies.
Implements the dependency inversion principle with proper lifecycle management.
"""

from typing import AsyncGenerator
from functools import lru_cache

from ..services.audio_processor import AudioProcessorService
from ..services.speech_to_text import SpeechToTextService
from ..services.text_to_speech import TextToSpeechService
from ..services.chat_service import ChatService
from ..services.session_manager import SessionManagerService
from ..models.database import db_manager
from .logging import get_logger

logger = get_logger(__name__)


class ServiceContainer:
    """Container for managing service dependencies and lifecycle."""
    
    def __init__(self):
        self._audio_processor: AudioProcessorService = None
        self._session_manager: SessionManagerService = None
        self._speech_to_text: SpeechToTextService = None
        self._text_to_speech: TextToSpeechService = None
        self._chat_service: ChatService = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize all services with proper dependency injection."""
        if self._initialized:
            return
        
        logger.info("Initializing service container")
        
        try:
            # Initialize database
            await db_manager.create_tables()
            
            # Initialize services in dependency order
            self._audio_processor = AudioProcessorService()
            self._session_manager = SessionManagerService()
            self._speech_to_text = SpeechToTextService(self._audio_processor)
            self._text_to_speech = TextToSpeechService()
            self._chat_service = ChatService(self._session_manager)
            
            self._initialized = True
            logger.info("Service container initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize service container", error=str(e))
            raise
    
    async def cleanup(self) -> None:
        """Clean up resources and close connections."""
        logger.info("Cleaning up service container")
        
        try:
            await db_manager.close()
            self._initialized = False
            logger.info("Service container cleaned up successfully")
            
        except Exception as e:
            logger.error("Error during service container cleanup", error=str(e))
    
    @property
    def audio_processor(self) -> AudioProcessorService:
        """Get audio processor service."""
        if not self._initialized:
            raise RuntimeError("Service container not initialized")
        return self._audio_processor
    
    @property
    def session_manager(self) -> SessionManagerService:
        """Get session manager service."""
        if not self._initialized:
            raise RuntimeError("Service container not initialized")
        return self._session_manager
    
    @property
    def speech_to_text(self) -> SpeechToTextService:
        """Get speech-to-text service."""
        if not self._initialized:
            raise RuntimeError("Service container not initialized")
        return self._speech_to_text
    
    @property
    def text_to_speech(self) -> TextToSpeechService:
        """Get text-to-speech service."""
        if not self._initialized:
            raise RuntimeError("Service container not initialized")
        return self._text_to_speech
    
    @property
    def chat_service(self) -> ChatService:
        """Get chat service."""
        if not self._initialized:
            raise RuntimeError("Service container not initialized")
        return self._chat_service


# Global service container instance
_service_container: ServiceContainer = None


@lru_cache()
def get_service_container() -> ServiceContainer:
    """Get the global service container instance."""
    global _service_container
    if _service_container is None:
        _service_container = ServiceContainer()
    return _service_container


# FastAPI dependency functions
async def get_audio_processor() -> AudioProcessorService:
    """FastAPI dependency for audio processor service."""
    container = get_service_container()
    return container.audio_processor


async def get_session_manager() -> SessionManagerService:
    """FastAPI dependency for session manager service."""
    container = get_service_container()
    return container.session_manager


async def get_speech_to_text() -> SpeechToTextService:
    """FastAPI dependency for speech-to-text service."""
    container = get_service_container()
    return container.speech_to_text


async def get_text_to_speech() -> TextToSpeechService:
    """FastAPI dependency for text-to-speech service."""
    container = get_service_container()
    return container.text_to_speech


async def get_chat_service() -> ChatService:
    """FastAPI dependency for chat service."""
    container = get_service_container()
    return container.chat_service


# Database session dependency
async def get_db_session() -> AsyncGenerator:
    """FastAPI dependency for database session."""
    async with db_manager.async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
