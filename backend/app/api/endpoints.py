"""
FastAPI endpoints for voice agent functionality.
Provides REST API endpoints for all voice interaction features.
"""

import tempfile
from typing import Dict, Any, Optional, List
from pathlib import Path

from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse, StreamingResponse

from ..core.dependencies import (
    get_audio_processor,
    get_speech_to_text,
    get_text_to_speech,
    get_chat_service,
    get_session_manager
)
from ..services.audio_processor import AudioProcessorService
from ..services.speech_to_text import SpeechToTextService
from ..services.text_to_speech import TextToSpeechService
from ..services.chat_service import ChatService
from ..services.session_manager import SessionManagerService
from ..models.schemas import (
    TextToSpeechRequest,
    TextToSpeechResponse,
    ChatRequest,
    ChatResponse,
    SpeechToTextResponse,
    VoiceInteractionResponse,
    ConversationSchema,
    ErrorResponse,
    MessageResponse
)
from ..core.exceptions import (
    VoiceAgentException,
    AudioProcessingError,
    SpeechToTextError,
    TextToSpeechError,
    GPTServiceError,
    SessionError
)
from ..core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/sessions", response_model=Dict[str, str])
async def create_session(
    session_manager: SessionManagerService = Depends(get_session_manager)
):
    """Create a new conversation session."""
    try:
        session_id = await session_manager.create_session()
        return {"session_id": session_id}
    except SessionError as e:
        logger.error("Failed to create session", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}", response_model=ConversationSchema)
async def get_session(
    session_id: str,
    session_manager: SessionManagerService = Depends(get_session_manager)
):
    """Get session information and conversation history."""
    try:
        session_data = await session_manager.get_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        history = await session_manager.get_conversation_history(session_id)
        
        return ConversationSchema(
            id=session_data["id"],
            status=session_data["status"],
            created_at=session_data["created_at"],
            updated_at=session_data["updated_at"],
            messages=[
                {
                    "id": msg["id"],
                    "session_id": session_id,
                    "type": msg["type"],
                    "content": msg["content"],
                    "timestamp": msg["timestamp"],
                    "extra_data": msg["extra_data"]
                }
                for msg in history
            ]
        )
    except SessionError as e:
        logger.error("Failed to get session", session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    session_manager: SessionManagerService = Depends(get_session_manager)
):
    """Delete a conversation session."""
    try:
        await session_manager.delete_session(session_id)
        return {"message": "Session deleted successfully"}
    except SessionError as e:
        logger.error("Failed to delete session", session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/speech-to-text", response_model=SpeechToTextResponse)
async def transcribe_audio(
    audio_file: UploadFile = File(...),
    language: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
    audio_processor: AudioProcessorService = Depends(get_audio_processor),
    speech_to_text: SpeechToTextService = Depends(get_speech_to_text)
):
    """Convert speech audio to text."""
    try:
        # Read audio data
        audio_data = await audio_file.read()
        
        # Get file format from filename
        file_format = Path(audio_file.filename).suffix.lower().lstrip('.')
        if not file_format:
            file_format = "wav"  # Default format
        
        # Validate audio
        await audio_processor.validate_audio(audio_data, file_format)
        
        # Transcribe audio
        result = await speech_to_text.transcribe_audio(audio_data, language)
        
        return SpeechToTextResponse(
            text=result["text"],
            confidence=result.get("confidence"),
            language=result.get("language"),
            duration=result.get("duration")
        )
        
    except AudioProcessingError as e:
        logger.error("Audio processing failed", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except SpeechToTextError as e:
        logger.error("Speech-to-text failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error("Unexpected error in speech-to-text", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/text-to-speech", response_model=TextToSpeechResponse)
async def synthesize_speech(
    request: TextToSpeechRequest,
    text_to_speech: TextToSpeechService = Depends(get_text_to_speech)
):
    """Convert text to speech audio."""
    try:
        # Generate speech
        audio_data = await text_to_speech.synthesize_speech(
            request.text,
            request.voice,
            request.language
        )

        logger.info(f"Audio data: {audio_data}")
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(
            suffix=".mp3",
            delete=False
        )
        temp_file.write(audio_data)
        temp_file.close()

        logger.info(f"Temp file: {temp_file.name}")
        
        # Return file response
        return FileResponse(
            path=temp_file.name,
            media_type="audio/mpeg",
            filename="speech.mp3"
        )
        
    except TextToSpeechError as e:
        logger.error("Text-to-speech failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error("Unexpected error in text-to-speech", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
    session_manager: SessionManagerService = Depends(get_session_manager)
):
    """Send a text message and get a response."""
    try:
        # Create session if not provided
        session_id = request.session_id
        if not session_id:
            session_id = await session_manager.create_session()
        
        # Generate response
        response_text, message_id = await chat_service.generate_response(
            request.message,
            session_id
        )
        
        return ChatResponse(
            message=response_text,
            session_id=session_id,
            message_id=message_id
        )
        
    except GPTServiceError as e:
        logger.error("Chat service failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
    except SessionError as e:
        logger.error("Session error in chat", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error("Unexpected error in chat", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/voice-interaction", response_model=VoiceInteractionResponse)
async def voice_interaction(
    audio_file: UploadFile = File(...),
    language: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
    voice: Optional[str] = Form("alloy"),
    audio_processor: AudioProcessorService = Depends(get_audio_processor),
    speech_to_text: SpeechToTextService = Depends(get_speech_to_text),
    chat_service: ChatService = Depends(get_chat_service),
    text_to_speech: TextToSpeechService = Depends(get_text_to_speech),
    session_manager: SessionManagerService = Depends(get_session_manager)
):
    """Complete voice interaction: speech-to-text -> chat -> text-to-speech."""
    try:
        # Create session if not provided
        if not session_id:
            session_id = await session_manager.create_session()
        
        # Read and validate audio
        audio_data = await audio_file.read()
        file_format = Path(audio_file.filename).suffix.lower().lstrip('.') or "wav"
        await audio_processor.validate_audio(audio_data, file_format)
        
        # Step 1: Speech to text
        transcription_result = await speech_to_text.transcribe_audio(audio_data, language)
        
        transcription_response = SpeechToTextResponse(
            text=transcription_result["text"],
            confidence=transcription_result.get("confidence"),
            language=transcription_result.get("language"),
            duration=transcription_result.get("duration")
        )
        
        # Step 2: Generate chat response
        response_text = await chat_service.generate_response(
            transcription_result["text"],
            session_id
        )
        
        # Get message ID
        history = await session_manager.get_conversation_history(session_id, limit=1)
        message_id = history[-1]["id"] if history else "unknown"
        
        chat_response = ChatResponse(
            message=response_text,
            session_id=session_id,
            message_id=message_id
        )
        
        # Step 3: Convert response to speech
        audio_response_data = await text_to_speech.synthesize_speech(
            response_text,
            voice,
            language
        )
        
        # Save audio response to temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        temp_file.write(audio_response_data)
        temp_file.close()
        
        audio_response = TextToSpeechResponse(
            audio_url=f"/download/{Path(temp_file.name).name}",
            duration=len(audio_response_data) / 1000,  # Rough estimate
            format="mp3"
        )
        
        return VoiceInteractionResponse(
            transcription=transcription_response,
            chat_response=chat_response,
            audio_response=audio_response
        )
        
    except (AudioProcessingError, SpeechToTextError, GPTServiceError, 
            TextToSpeechError, SessionError) as e:
        logger.error("Voice interaction failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error("Unexpected error in voice interaction", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/sessions/{session_id}/summary")
async def get_conversation_summary(
    session_id: str,
    chat_service: ChatService = Depends(get_chat_service)
):
    """Get a summary of the conversation."""
    try:
        summary = await chat_service.summarize_conversation(session_id)
        return {"summary": summary}
    except GPTServiceError as e:
        logger.error("Failed to summarize conversation", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions/{session_id}/insights")
async def get_conversation_insights(
    session_id: str,
    chat_service: ChatService = Depends(get_chat_service)
):
    """Get insights about the conversation."""
    try:
        insights = await chat_service.get_conversation_insights(session_id)
        return insights
    except Exception as e:
        logger.error("Failed to get conversation insights", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check(
    audio_processor: AudioProcessorService = Depends(get_audio_processor),
    speech_to_text: SpeechToTextService = Depends(get_speech_to_text),
    text_to_speech: TextToSpeechService = Depends(get_text_to_speech),
    chat_service: ChatService = Depends(get_chat_service),
    session_manager: SessionManagerService = Depends(get_session_manager)
):
    """Check the health of all services."""
    try:
        health_data = {
            "status": "healthy",
            "services": {
                "audio_processor": await audio_processor.health_check(),
                "speech_to_text": await speech_to_text.health_check(),
                "text_to_speech": await text_to_speech.health_check(),
                "chat_service": await chat_service.health_check(),
                "session_manager": await session_manager.health_check()
            }
        }
        
        # Check if any service is unhealthy
        for service_health in health_data["services"].values():
            if service_health.get("status") != "healthy":
                health_data["status"] = "degraded"
                break
        
        return health_data
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.get("/stats")
async def get_system_stats(
    session_manager: SessionManagerService = Depends(get_session_manager)
):
    """Get system statistics."""
    try:
        stats = await session_manager.get_session_statistics()
        return stats
    except Exception as e:
        logger.error("Failed to get system stats", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
