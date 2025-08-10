"""
WebSocket endpoints for real-time voice interaction.
Provides streaming audio processing and real-time conversation.
"""

import json
import base64
from typing import Dict, Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from websockets.exceptions import ConnectionClosed

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
    WebSocketMessage,
    AudioChunkMessage,
    TranscriptionMessage,
    ResponseMessage
)
from ..core.logging import get_logger
from ..core.exceptions import VoiceAgentException

logger = get_logger(__name__)
router = APIRouter()


class WebSocketManager:
    """Manages WebSocket connections and message handling."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_connections: Dict[str, str] = {}  # session_id -> connection_id
        
    async def connect(self, websocket: WebSocket, connection_id: str) -> None:
        """Accept a WebSocket connection."""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        logger.info("WebSocket connected", connection_id=connection_id)
    
    def disconnect(self, connection_id: str) -> None:
        """Remove a WebSocket connection."""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
        
        # Remove session mapping
        for session_id, conn_id in list(self.session_connections.items()):
            if conn_id == connection_id:
                del self.session_connections[session_id]
        
        logger.info("WebSocket disconnected", connection_id=connection_id)
    
    async def send_message(self, connection_id: str, message: Dict[str, Any]) -> None:
        """Send a message to a specific connection."""
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                await websocket.send_text(json.dumps(message))
            except (ConnectionClosed, WebSocketDisconnect):
                self.disconnect(connection_id)
    
    def associate_session(self, session_id: str, connection_id: str) -> None:
        """Associate a session with a connection."""
        self.session_connections[session_id] = connection_id
    
    def get_connection_by_session(self, session_id: str) -> str:
        """Get connection ID by session ID."""
        return self.session_connections.get(session_id)


# Global WebSocket manager
websocket_manager = WebSocketManager()


@router.websocket("/ws/{connection_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    connection_id: str,
    audio_processor: AudioProcessorService = Depends(get_audio_processor),
    speech_to_text: SpeechToTextService = Depends(get_speech_to_text),
    text_to_speech: TextToSpeechService = Depends(get_text_to_speech),
    chat_service: ChatService = Depends(get_chat_service),
    session_manager: SessionManagerService = Depends(get_session_manager)
):
    """WebSocket endpoint for real-time voice interaction."""
    await websocket_manager.connect(websocket, connection_id)
    session_id = None
    audio_chunks = []
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            message_type = message_data.get("type")
            
            if message_type == "initialize_session":
                # Create new session
                session_id = await session_manager.create_session()
                websocket_manager.associate_session(session_id, connection_id)
                
                await websocket_manager.send_message(connection_id, {
                    "type": "session_initialized",
                    "session_id": session_id
                })
                
                logger.info("Session initialized for WebSocket", 
                           session_id=session_id, connection_id=connection_id)
            
            elif message_type == "audio_chunk":
                # Handle audio chunk
                await handle_audio_chunk(
                    message_data, 
                    audio_chunks, 
                    connection_id, 
                    audio_processor,
                    speech_to_text,
                    chat_service,
                    text_to_speech,
                    session_id
                )
            
            elif message_type == "text_message":
                # Handle text message
                await handle_text_message(
                    message_data,
                    connection_id,
                    chat_service,
                    text_to_speech,
                    session_id
                )
            
            elif message_type == "end_audio":
                # Process accumulated audio chunks
                if audio_chunks and session_id:
                    await process_complete_audio(
                        audio_chunks,
                        connection_id,
                        audio_processor,
                        speech_to_text,
                        chat_service,
                        text_to_speech,
                        session_id
                    )
                audio_chunks = []
            
            elif message_type == "ping":
                # Handle ping/pong for connection health
                await websocket_manager.send_message(connection_id, {
                    "type": "pong"
                })
            
            else:
                # Unknown message type
                await websocket_manager.send_message(connection_id, {
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                })
    
    except WebSocketDisconnect:
        websocket_manager.disconnect(connection_id)
        logger.info("WebSocket disconnected normally", connection_id=connection_id)
    
    except Exception as e:
        logger.error("WebSocket error", connection_id=connection_id, error=str(e))
        try:
            await websocket_manager.send_message(connection_id, {
                "type": "error",
                "message": str(e)
            })
        except:
            pass
        websocket_manager.disconnect(connection_id)


async def handle_audio_chunk(
    message_data: Dict[str, Any],
    audio_chunks: list,
    connection_id: str,
    audio_processor: AudioProcessorService,
    speech_to_text: SpeechToTextService,
    chat_service: ChatService,
    text_to_speech: TextToSpeechService,
    session_id: str
) -> None:
    """Handle incoming audio chunk."""
    try:
        audio_data_b64 = message_data.get("audio_data")
        is_final = message_data.get("is_final", False)
        
        if not audio_data_b64:
            await websocket_manager.send_message(connection_id, {
                "type": "error",
                "message": "No audio data provided"
            })
            return
        
        # Decode base64 audio data
        audio_data = base64.b64decode(audio_data_b64)
        audio_chunks.append(audio_data)
        
        # For streaming recognition, you could process chunks incrementally
        # For now, we'll wait for the final chunk
        if is_final and session_id:
            await process_complete_audio(
                audio_chunks,
                connection_id,
                audio_processor,
                speech_to_text,
                chat_service,
                text_to_speech,
                session_id
            )
            audio_chunks.clear()
        
        # Send acknowledgment
        await websocket_manager.send_message(connection_id, {
            "type": "audio_chunk_received",
            "chunk_number": len(audio_chunks),
            "is_final": is_final
        })
        
    except Exception as e:
        logger.error("Error handling audio chunk", error=str(e))
        await websocket_manager.send_message(connection_id, {
            "type": "error",
            "message": f"Audio processing error: {str(e)}"
        })


async def handle_text_message(
    message_data: Dict[str, Any],
    connection_id: str,
    chat_service: ChatService,
    text_to_speech: TextToSpeechService,
    session_id: str
) -> None:
    """Handle incoming text message."""
    try:
        text = message_data.get("text")
        if not text or not session_id:
            await websocket_manager.send_message(connection_id, {
                "type": "error",
                "message": "No text provided or session not initialized"
            })
            return
        
        # Generate response
        response_text = await chat_service.generate_response(text, session_id)
        
        # Send text response
        await websocket_manager.send_message(connection_id, {
            "type": "text_response",
            "text": response_text
        })
        
        # Generate audio response if requested
        if message_data.get("include_audio", False):
            voice = message_data.get("voice", "alloy")
            audio_data = await text_to_speech.synthesize_speech(response_text, voice)
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')
            
            await websocket_manager.send_message(connection_id, {
                "type": "audio_response",
                "audio_data": audio_b64,
                "format": "mp3"
            })
        
    except Exception as e:
        logger.error("Error handling text message", error=str(e))
        await websocket_manager.send_message(connection_id, {
            "type": "error",
            "message": f"Text processing error: {str(e)}"
        })


async def process_complete_audio(
    audio_chunks: list,
    connection_id: str,
    audio_processor: AudioProcessorService,
    speech_to_text: SpeechToTextService,
    chat_service: ChatService,
    text_to_speech: TextToSpeechService,
    session_id: str
) -> None:
    """Process complete audio from chunks."""
    try:
        # Combine audio chunks
        combined_audio = b"".join(audio_chunks)
        
        if not combined_audio:
            return
        
        # Validate audio
        await audio_processor.validate_audio(combined_audio, "wav")
        
        # Send transcription start notification
        await websocket_manager.send_message(connection_id, {
            "type": "transcription_started"
        })
        
        # Transcribe audio
        transcription_result = await speech_to_text.transcribe_audio(combined_audio)
        
        # Send transcription result
        await websocket_manager.send_message(connection_id, {
            "type": "transcription_completed",
            "text": transcription_result["text"],
            "confidence": transcription_result.get("confidence"),
            "language": transcription_result.get("language")
        })
        
        # Generate chat response
        await websocket_manager.send_message(connection_id, {
            "type": "response_generation_started"
        })
        
        response_text = await chat_service.generate_response(
            transcription_result["text"], 
            session_id
        )
        
        # Send text response
        await websocket_manager.send_message(connection_id, {
            "type": "text_response",
            "text": response_text
        })
        
        # Generate audio response
        await websocket_manager.send_message(connection_id, {
            "type": "audio_generation_started"
        })
        
        audio_response = await text_to_speech.synthesize_speech(response_text)
        audio_b64 = base64.b64encode(audio_response).decode('utf-8')
        
        # Send audio response
        await websocket_manager.send_message(connection_id, {
            "type": "audio_response",
            "audio_data": audio_b64,
            "format": "mp3"
        })
        
        # Send completion notification
        await websocket_manager.send_message(connection_id, {
            "type": "interaction_completed"
        })
        
    except VoiceAgentException as e:
        logger.error("Voice agent error processing audio", error=str(e))
        await websocket_manager.send_message(connection_id, {
            "type": "error",
            "message": str(e),
            "error_code": e.error_code
        })
    
    except Exception as e:
        logger.error("Unexpected error processing audio", error=str(e))
        await websocket_manager.send_message(connection_id, {
            "type": "error",
            "message": f"Processing error: {str(e)}"
        })


@router.get("/ws/stats")
async def get_websocket_stats():
    """Get WebSocket connection statistics."""
    return {
        "active_connections": len(websocket_manager.active_connections),
        "active_sessions": len(websocket_manager.session_connections)
    }
