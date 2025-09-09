# Speech-to-Text Microservice

This microservice provides speech-to-text conversion using OpenAI's Whisper model.

## Features

- Real-time audio transcription using Whisper
- Support for multiple languages
- Optimized for chat interface integration
- RESTful API with FastAPI
- CORS enabled for frontend integration

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the service:
```bash
python app.py
```

The service will be available at `http://localhost:8001`

## API Endpoints

### Health Check
- `GET /health` - Service health status

### Transcription
- `POST /transcribe` - General transcription endpoint
- `POST /transcribe-chat` - Optimized for chat interface

## Usage

Send audio files (WAV, MP3, etc.) to the transcription endpoints:

```bash
curl -X POST "http://localhost:8001/transcribe-chat" \
  -H "Content-Type: multipart/form-data" \
  -F "audio_file=@audio.wav" \
  -F "language=fa"
```

## Integration

This service is designed to be called from:
- Frontend: Direct audio upload from chat interface
- Backend: Integration with main LangExtract service

## Configuration

- Default model: `base` (good balance of speed and accuracy)
- Default language: `fa` (Persian) for chat interface
- Port: 8001
