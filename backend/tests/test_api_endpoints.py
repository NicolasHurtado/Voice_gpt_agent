"""
Tests for API endpoints.
"""

import json
from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient


class TestSessionEndpoints:
    """Test session management endpoints."""
    
    @pytest.mark.asyncio
    async def test_create_session(self, client: AsyncClient):
        """Test session creation."""
        response = await client.post("/api/v1/sessions")
        assert response.status_code == 200
        
        data = response.json()
        assert "session_id" in data
        assert len(data["session_id"]) > 0
    
    @pytest.mark.asyncio
    async def test_get_session(self, client: AsyncClient, test_session_id: str):
        """Test getting session information."""
        response = await client.get(f"/api/v1/sessions/{test_session_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == test_session_id
        assert "created_at" in data
        assert "updated_at" in data
        assert "status" in data
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self, client: AsyncClient):
        """Test getting a non-existent session."""
        response = await client.get("/api/v1/sessions/nonexistent")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_delete_session(self, client: AsyncClient, test_session_id: str):
        """Test session deletion."""
        response = await client.delete(f"/api/v1/sessions/{test_session_id}")
        assert response.status_code == 200
        
        # Verify session is deleted
        response = await client.get(f"/api/v1/sessions/{test_session_id}")
        assert response.status_code == 404


class TestChatEndpoints:
    """Test chat functionality endpoints."""
    
    @pytest.mark.asyncio
    @patch('app.services.chat_service.ChatService.generate_response')
    async def test_chat_message(self, mock_generate, client: AsyncClient, test_session_id: str):
        """Test sending a chat message."""
        mock_generate.return_value = ("Test response from AI", "test-message-id-12345")
        
        response = await client.post(
            "/api/v1/chat",
            json={
                "message": "Hello, AI!",
                "session_id": test_session_id
            }
        )

        print("response.json()", response.json())
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Test response from AI"
        assert data["session_id"] == test_session_id
        assert data["message_id"] == "test-message-id-12345"
        assert data["message_id"] != "unknown"
    
    @pytest.mark.asyncio
    async def test_chat_without_session(self, client: AsyncClient):
        """Test chat message without session ID (should create new session)."""
        with patch('app.services.chat_service.ChatService.generate_response') as mock_generate:
            mock_generate.return_value = ("Test response", "test-message-id-67890")
            
            response = await client.post(
                "/api/v1/chat",
                json={"message": "Hello!"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "session_id" in data
            assert data["message"] == "Test response"


class TestAudioEndpoints:
    """Test audio processing endpoints."""
    
    @pytest.mark.asyncio
    @patch('app.services.speech_to_text.SpeechToTextService.transcribe_audio')
    async def test_speech_to_text(self, mock_transcribe, client: AsyncClient, sample_audio_data: bytes):
        """Test speech-to-text endpoint."""
        mock_transcribe.return_value = {
            "text": "Hello world",
            "confidence": 0.95,
            "language": "en",
            "duration": 2.0
        }
        
        files = {"audio_file": ("test.wav", sample_audio_data, "audio/wav")}
        response = await client.post("/api/v1/speech-to-text", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["text"] == "Hello world"
        assert data["confidence"] == 0.95
    
    @pytest.mark.asyncio
    @patch('app.services.text_to_speech.TextToSpeechService.synthesize_speech')
    async def test_text_to_speech(self, mock_synthesize, client: AsyncClient):
        """Test text-to-speech endpoint."""
        mock_synthesize.return_value = b"fake_audio_data"
        
        response = await client.post(
            "/api/v1/text-to-speech",
            json={
                "text": "Hello world",
                "voice": "alloy"
            }
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "audio/mpeg"


class TestHealthEndpoints:
    """Test health and monitoring endpoints."""
    
    @pytest.mark.asyncio
    async def test_simple_health_check(self, client: AsyncClient):
        """Test simple health check endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
    
    @patch('app.services.audio_processor.AudioProcessorService.health_check')
    @patch('app.services.speech_to_text.SpeechToTextService.health_check')
    @patch('app.services.text_to_speech.TextToSpeechService.health_check')
    @patch('app.services.chat_service.ChatService.health_check')
    @patch('app.services.session_manager.SessionManagerService.health_check')
    @pytest.mark.asyncio
    async def test_detailed_health_check(
        self, 
        mock_session_health,
        mock_chat_health,
        mock_tts_health,
        mock_stt_health,
        mock_audio_health,
        client: AsyncClient
    ):
        """Test detailed health check endpoint."""
        # Mock all service health checks
        mock_audio_health.return_value = {"service": "AudioProcessor", "status": "healthy"}
        mock_stt_health.return_value = {"service": "SpeechToText", "status": "healthy"}
        mock_tts_health.return_value = {"service": "TextToSpeech", "status": "healthy"}
        mock_chat_health.return_value = {"service": "ChatService", "status": "healthy"}
        mock_session_health.return_value = {"service": "SessionManager", "status": "healthy"}
        
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "services" in data
        assert len(data["services"]) == 5
    
    @pytest.mark.asyncio
    async def test_system_stats(self, client: AsyncClient):
        """Test system statistics endpoint."""
        with patch('app.services.session_manager.SessionManagerService.get_session_statistics') as mock_stats:
            mock_stats.return_value = {
                "total_sessions": 5,
                "active_sessions": 2,
                "total_messages": 20
            }
            
            response = await client.get("/api/v1/stats")
            assert response.status_code == 200
            
            data = response.json()
            assert data["total_sessions"] == 5
            assert data["active_sessions"] == 2
            assert data["total_messages"] == 20


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.mark.asyncio
    async def test_invalid_audio_file(self, client: AsyncClient):
        """Test uploading invalid audio file."""
        files = {"audio_file": ("test.txt", b"not audio data", "text/plain")}
        response = await client.post("/api/v1/speech-to-text", files=files)
        
        # Should return error due to invalid audio format
        assert response.status_code in [400, 500]
    
    @pytest.mark.asyncio
    async def test_missing_openai_key(self, client: AsyncClient):
        """Test behavior with missing OpenAI API key."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': ''}):
            response = await client.post(
                "/api/v1/text-to-speech",
                json={"text": "Test"}
            )
            # Should handle missing API key gracefully
            assert response.status_code in [400, 500]
    
    @pytest.mark.asyncio
    async def test_large_text_input(self, client: AsyncClient):
        """Test handling of very large text input."""
        large_text = "A" * 10000  # 10KB of text
        
        response = await client.post(
            "/api/v1/text-to-speech",
            json={"text": large_text}
        )
    
        assert response.status_code == 422
        assert response.json()['detail'][0]['type'] == "string_too_long"


class TestInputValidation:
    """Test input validation."""
    
    @pytest.mark.asyncio
    async def test_empty_chat_message(self, client: AsyncClient):
        """Test sending empty chat message."""
        response = await client.post(
            "/api/v1/chat",
            json={"message": ""}
        )
        
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_invalid_session_id_format(self, client: AsyncClient):
        """Test using invalid session ID format."""
        response = await client.get("/api/v1/sessions/invalid-format-123")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_missing_required_fields(self, client: AsyncClient):
        """Test API calls with missing required fields."""
        # Chat without message
        response = await client.post("/api/v1/chat", json={})
        assert response.status_code == 422
        
        # TTS without text
        response = await client.post("/api/v1/text-to-speech", json={})
        assert response.status_code == 422
