"""
Application configuration management using Pydantic Settings.
Follows the 12-factor app methodology for configuration.
"""

from typing import List
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseModel):
    """Database configuration settings."""
    url: str = "sqlite+aiosqlite:///./voice_agent.db"


class OpenAISettings(BaseModel):
    """OpenAI API configuration settings."""
    api_key: str
    model: str = "gpt-oss:20b"
    whisper_model: str = "whisper-1"
    tts_model: str = "tts-1"
    tts_voice: str = "alloy"


class AudioSettings(BaseModel):
    """Audio processing configuration settings."""
    max_size_mb: int = 25
    supported_formats: List[str] = ["wav", "mp3", "m4a", "webm", "mp4"]
    sample_rate: int = 16000


class APISettings(BaseModel):
    """API server configuration settings."""
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]


class SessionSettings(BaseModel):
    """Session management configuration settings."""
    timeout_minutes: int = 30
    max_conversation_history: int = 10


class Settings(BaseSettings):
    """Main application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application metadata
    app_name: str = "Voice-enabled GPT Agent"
    app_version: str = "1.0.0"
    debug: bool = True
    log_level: str = "INFO"
    
    # OpenAI configuration
    openai_api_key: str = "sk-placeholder-key"
    openai_model: str = "gpt-oss:20b"
    whisper_model: str = "whisper-1"
    tts_model: str = "tts-1"
    tts_voice: str = "alloy"
    
    # Database configuration
    database_url: str = "sqlite+aiosqlite:///./voice_agent.db"
    
    # Audio configuration
    max_audio_size_mb: int = 25
    supported_audio_formats: str = "wav,mp3,m4a,webm,mp4"
    audio_sample_rate: int = 16000
    
    # API configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:3000,http://localhost:8080"
    
    # Session configuration
    session_timeout_minutes: int = 30
    max_conversation_history: int = 10
    
    @property
    def openai_settings(self) -> OpenAISettings:
        """Get OpenAI configuration as a structured object."""
        return OpenAISettings(
            api_key=self.openai_api_key,
            model=self.openai_model,
            whisper_model=self.whisper_model,
            tts_model=self.tts_model,
            tts_voice=self.tts_voice
        )
    
    @property
    def database_settings(self) -> DatabaseSettings:
        """Get database configuration as a structured object."""
        return DatabaseSettings(url=self.database_url)
    
    @property
    def audio_settings(self) -> AudioSettings:
        """Get audio configuration as a structured object."""
        return AudioSettings(
            max_size_mb=self.max_audio_size_mb,
            supported_formats=self.supported_audio_formats.split(","),
            sample_rate=self.audio_sample_rate
        )
    
    @property
    def api_settings(self) -> APISettings:
        """Get API configuration as a structured object."""
        return APISettings(
            host=self.api_host,
            port=self.api_port,
            cors_origins=self.cors_origins.split(",")
        )
    
    @property
    def session_settings(self) -> SessionSettings:
        """Get session configuration as a structured object."""
        return SessionSettings(
            timeout_minutes=self.session_timeout_minutes,
            max_conversation_history=self.max_conversation_history
        )


# Global settings instance
settings = Settings()
