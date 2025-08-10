"""
Pydantic schemas for request/response validation and serialization.
Provides type safety and automatic validation for API endpoints.
"""

from datetime import datetime
from typing import List, Optional
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class MessageType(str, Enum):
    """Types of messages in a conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationStatus(str, Enum):
    """Status of a conversation session."""
    ACTIVE = "active"
    COMPLETED = "completed"
    EXPIRED = "expired"


class AudioFormat(str, Enum):
    """Supported audio formats."""
    WAV = "wav"
    MP3 = "mp3"
    M4A = "m4a"
    WEBM = "webm"
    MP4 = "mp4"


# Request Schemas
class VoiceRequestBase(BaseModel):
    """Base schema for voice requests."""
    session_id: Optional[str] = Field(None, description="Session ID for conversation context")
    language: Optional[str] = Field("en", description="Language code for processing")


class TextToSpeechRequest(VoiceRequestBase):
    """Request schema for text-to-speech conversion."""
    text: str = Field(..., min_length=1, max_length=4096, description="Text to convert to speech")
    voice: Optional[str] = Field("alloy", description="Voice to use for speech synthesis")


class ChatRequest(VoiceRequestBase):
    """Request schema for text-based chat."""
    message: str = Field(..., min_length=1, max_length=2000, description="User message")


# Response Schemas
class MessageSchema(BaseModel):
    """Schema for a conversation message."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    session_id: str
    type: MessageType
    content: str
    timestamp: datetime
    extra_data: Optional[dict] = None


class MessageResponse(BaseModel):
    """Schema for a conversation message."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    type: MessageType
    content: str
    timestamp: datetime
    extra_data: Optional[dict] = None

class ConversationSchema(BaseModel):
    """Schema for a conversation session."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    status: ConversationStatus
    created_at: datetime
    updated_at: datetime


class SpeechToTextResponse(BaseModel):
    """Response schema for speech-to-text conversion."""
    text: str = Field(..., description="Transcribed text from audio")
    confidence: Optional[float] = Field(None, description="Confidence score of transcription")
    language: Optional[str] = Field(None, description="Detected language")
    duration: Optional[float] = Field(None, description="Audio duration in seconds")


class TextToSpeechResponse(BaseModel):
    """Response schema for text-to-speech conversion."""
    audio_url: str = Field(..., description="URL to download the generated audio")
    duration: Optional[float] = Field(None, description="Audio duration in seconds")
    format: AudioFormat = Field(AudioFormat.MP3, description="Audio format")


class ChatResponse(BaseModel):
    """Response schema for chat interactions."""
    message: str = Field(..., description="Assistant's response")
    session_id: str = Field(..., description="Session ID for conversation context")
    message_id: str = Field(..., description="Unique message identifier")


class VoiceInteractionResponse(BaseModel):
    """Response schema for complete voice interaction."""
    transcription: SpeechToTextResponse
    chat_response: ChatResponse
    audio_response: TextToSpeechResponse


class ErrorResponse(BaseModel):
    """Schema for error responses."""
    error: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    details: Optional[dict] = Field(None, description="Additional error details")


class HealthResponse(BaseModel):
    """Schema for health check response."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(..., description="Current server time")


# WebSocket Schemas
class WebSocketMessage(BaseModel):
    """Base schema for WebSocket messages."""
    type: str = Field(..., description="Message type")
    data: dict = Field(default_factory=dict, description="Message data")


class AudioChunkMessage(WebSocketMessage):
    """Schema for audio chunk messages over WebSocket."""
    type: str = Field("audio_chunk", description="Message type")
    audio_data: str = Field(..., description="Base64 encoded audio data")
    is_final: bool = Field(False, description="Whether this is the final chunk")


class TranscriptionMessage(WebSocketMessage):
    """Schema for transcription messages over WebSocket."""
    type: str = Field("transcription", description="Message type")
    text: str = Field(..., description="Transcribed text")
    is_partial: bool = Field(False, description="Whether this is a partial transcription")


class ResponseMessage(WebSocketMessage):
    """Schema for assistant response messages over WebSocket."""
    type: str = Field("response", description="Message type")
    text: str = Field(..., description="Assistant response text")
    audio_url: Optional[str] = Field(None, description="URL for audio response")
