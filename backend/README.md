# 🎤 Voice-Enabled AI Agent

A FastAPI-based voice interaction system with speech-to-text, AI chat, and text-to-speech capabilities.

## ✨ Features

- 🎙️ **Speech-to-Text**: Audio transcription using OpenAI Whisper
- 🤖 **AI Chat**: Contextual conversations with GPT/Local AI models
- 🔊 **Text-to-Speech**: Natural voice synthesis
- ⚡ **Real-time**: WebSocket support for streaming interactions
- 💾 **Sessions**: Persistent conversation history
- 🌐 **REST API**: Complete API for all functionality

## 🛠️ Tech Stack

- **Backend**: FastAPI + Python 3.11+
- **AI**: OpenAI GPT-4, Whisper, TTS / Local AI (Ollama)
- **Database**: SQLite with async SQLAlchemy
- **Audio**: pydub, soundfile processing

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- OpenAI API key (optional - supports local AI)

### Installation

```bash
# 1. Install dependencies
cd backend
pip install -r requirements.txt

# 2. Set environment variables
cp env.example .env
# Edit .env and add your OpenAI API key

# 3. Run the application
uvicorn app.main:app --reload
```

### Access
- **Frontend**: http://localhost:8000/static/index.html
- **API Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/health

### Environment Variables

```bash
# Required for OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Optional
OPENAI_MODEL=gpt-4-turbo-preview
DATABASE_URL=sqlite+aiosqlite:///./voice_agent.db
```

## 📖 API Endpoints

### Core APIs
- `POST /api/v1/sessions` - Create session
- `POST /api/v1/chat` - Send text message
- `POST /api/v1/speech-to-text` - Transcribe audio
- `POST /api/v1/text-to-speech` - Generate speech
- `POST /api/v1/voice-interaction` - Complete voice workflow

### WebSocket
- `ws://localhost:8000/api/v1/ws/{connection_id}` - Real-time interaction

## 🎯 Usage Example

```python
import requests

# Create session
response = requests.post("http://localhost:8000/api/v1/sessions")
session_id = response.json()["session_id"]

# Send text message
response = requests.post(
    "http://localhost:8000/api/v1/chat",
    json={"message": "Hello!", "session_id": session_id}
)
print(response.json()["message"])

# Voice interaction
with open("audio.wav", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/v1/voice-interaction",
        files={"audio_file": f},
        data={"session_id": session_id}
    )
```

## 🛠️ Development

### Project Structure
```
backend/
├── app/
│   ├── api/          # API endpoints
│   ├── core/         # Configuration & dependencies
│   ├── models/       # Database & Pydantic schemas  
│   ├── services/     # Business logic
│   └── main.py       # Application entry point
├── static/           # Frontend files
└── tests/           # Test files
```

### Testing
```bash
pytest                    # Run all tests
pytest --cov=app tests/  # With coverage
```

## 📝 License

MIT License - see LICENSE file for details.

---

Built with FastAPI and modern AI technologies.
