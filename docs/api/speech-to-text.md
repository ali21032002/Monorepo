# Speech-to-Text API Reference

The Speech-to-Text Service provides endpoints for converting speech to text using hybrid Persian models.

## Base URL

```
http://localhost:8001
```

## Endpoints

### POST /transcribe

Basic speech-to-text conversion.

**Request:** Multipart form data with `audio` file

**Response:**
```json
{
  "text": "transcribed text",
  "confidence": 0.95
}
```

### POST /transcribe-chat

Optimized for chat interface.

### POST /transcribe-hybrid

Hybrid Persian models for maximum accuracy.

### GET /models

List available speech models.

### GET /health

Service health check.

### GET /diagnose

System environment diagnostics.

## Interactive Documentation

Visit http://localhost:8001/docs for interactive Swagger UI documentation.

