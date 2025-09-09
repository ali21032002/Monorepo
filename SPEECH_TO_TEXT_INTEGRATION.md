# Speech-to-Text Integration

This document describes the new speech-to-text microservice integration with the LangExtract system.

## Overview

A new microservice has been added that converts speech to text using OpenAI's Whisper model. The service integrates seamlessly with the existing chatbot functionality, allowing users to record voice messages that are automatically transcribed and sent to the chat.

## Architecture

```
Frontend (React) 
    ↓ (Audio Recording)
Speech-to-Text Service (Whisper)
    ↓ (Transcribed Text)
Main Backend (LangExtract)
    ↓ (Chat Response)
Frontend (Display)
```

## Components

### 1. Speech-to-Text Microservice (`monorepo/speechToText/`)

- **Port**: 8001
- **Technology**: FastAPI + Whisper
- **Endpoints**:
  - `GET /health` - Health check
  - `POST /transcribe` - General transcription
  - `POST /transcribe-chat` - Optimized for chat (defaults to Persian)

### 2. Frontend Integration

- Updated voice recording functionality in `App.tsx`
- Audio is sent directly to speech-to-text service
- Transcribed text is automatically sent to chat
- Error handling for transcription failures

### 3. Backend Integration

- New endpoint: `POST /api/speech-to-text`
- Proxies requests to speech-to-text microservice
- Added `httpx` dependency for HTTP client

## Usage

### Starting the Services

#### Option 1: Using the startup script
```bash
python start_services.py
```

#### Option 2: Using Docker Compose
```bash
docker-compose up
```

#### Option 3: Manual startup
```bash
# Terminal 1 - Speech-to-Text Service
cd monorepo/speechToText
pip install -r requirements.txt
python app.py

# Terminal 2 - Main Backend
cd monorepo/backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 3 - Frontend
cd monorepo/frontend
npm install
npm run dev
```

### Using Voice Chat

1. Navigate to the "دستیار هوشمند" (Smart Assistant) tab
2. Click the "🎙 ضبط" (Record) button
3. Speak your message
4. Click "⏹ توقف" (Stop) to finish recording
5. The audio will be automatically transcribed and sent to the chat
6. The AI will respond to your transcribed message

## Configuration

### Speech-to-Text Service

- **Model Size**: `base` (good balance of speed and accuracy)
- **Default Language**: `fa` (Persian) for chat interface
- **Supported Languages**: All languages supported by Whisper

### Environment Variables

- `PYTHONUNBUFFERED=1` - For proper logging
- `VITE_API_URL` - Backend API URL (Frontend)
- `VITE_SPEECH_URL` - Speech-to-Text service URL (Frontend)

## API Reference

### Speech-to-Text Service

#### POST /transcribe-chat
Convert audio to text for chat interface.

**Request:**
```bash
curl -X POST "http://localhost:8001/transcribe-chat" \
  -H "Content-Type: multipart/form-data" \
  -F "audio_file=@recording.wav" \
  -F "language=fa"
```

**Response:**
```json
{
  "text": "متن تبدیل شده از صدا",
  "language": "fa",
  "confidence": 0.95
}
```

### Main Backend

#### POST /api/speech-to-text
Proxy endpoint for speech-to-text service.

**Request:**
```bash
curl -X POST "http://localhost:8000/api/speech-to-text" \
  -H "Content-Type: multipart/form-data" \
  -F "audio_file=@recording.wav" \
  -F "language=fa" \
  -F "model_size=base"
```

## Error Handling

- **Microphone Access**: Browser permission required
- **Service Unavailable**: Graceful fallback with error message
- **Transcription Failure**: User-friendly error messages in Persian
- **Network Issues**: Timeout handling and retry logic

## Performance Considerations

- **Model Loading**: Whisper model is loaded once and cached
- **Audio Format**: WAV format recommended for best compatibility
- **File Size**: Large audio files may take longer to process
- **Concurrent Requests**: Service handles multiple requests efficiently

## Security

- **CORS**: Configured for development (should be restricted in production)
- **File Validation**: Audio file type validation
- **Temporary Files**: Automatic cleanup of uploaded files

## Troubleshooting

### Common Issues

1. **"دسترسی به میکروفون امکان‌پذیر نیست"**
   - Grant microphone permission in browser
   - Check browser security settings

2. **"خطا در تبدیل صدا به متن"**
   - Check if speech-to-text service is running
   - Verify network connectivity
   - Check service logs

3. **Service not starting**
   - Install dependencies: `pip install -r requirements.txt`
   - Check port availability (8001)
   - Verify Python version (3.11+)

### Logs

- Speech-to-Text service logs: Console output
- Main backend logs: Console output
- Frontend errors: Browser console

## Future Enhancements

- [ ] Real-time streaming transcription
- [ ] Multiple language detection
- [ ] Audio quality validation
- [ ] Transcription confidence indicators
- [ ] Voice command recognition
- [ ] Audio preprocessing for better accuracy
