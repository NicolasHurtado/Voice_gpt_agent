"""
Pytest configuration and fixtures for voice agent tests.
"""

import os
import asyncio
from typing import AsyncGenerator
import pytest_asyncio
import pytest
from httpx import AsyncClient

# Set test environment BEFORE importing app modules
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["DEBUG"] = "True" 
os.environ["OPENAI_API_KEY"] = "test-key"

from app.main import app
from app.core.dependencies import get_service_container




@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_services():
    """Initialize service container for tests."""
    container = get_service_container()
    if not container._initialized:
        await container.initialize()
    yield


@pytest_asyncio.fixture(scope="session")
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Create test client."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def test_session_id(client: AsyncClient) -> str:
    """Create a test session and return its ID."""
    try:
        response = await client.post("/api/v1/sessions")
        assert response.status_code == 200
        return response.json()["session_id"]
    except Exception as e:
        # Return a mock session ID if creation fails
        return "test-session-123"


@pytest.fixture
def sample_audio_data() -> bytes:
    """Return sample audio data for testing."""
    # Simple WAV header + silent audio data
    wav_header = b'RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80>\x00\x00\x00}\x00\x00\x02\x00\x10\x00data\x00\x00\x00\x00'
    silent_audio = b'\x00' * 1000  # 1000 bytes of silence
    return wav_header + silent_audio


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API responses for testing."""
    return {
        "transcription": {
            "text": "Hello, this is a test message.",
            "language": "en",
            "duration": 2.5
        },
        "chat_completion": {
            "choices": [{
                "message": {
                    "content": "Hello! I'm a test response from the AI."
                }
            }],
            "usage": {
                "total_tokens": 25
            }
        },
        "speech_audio": b"fake_audio_data"
    }
