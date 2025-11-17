# Backend API Reference

The Backend Service provides a FastAPI-based REST API for text extraction and analysis.

## Base URL

```
http://localhost:8000
```

## Endpoints

### POST /api/extract

Extract entities and relationships from text.

**Request Body:**
```json
{
  "text": "string",
  "language": "fa" | "en",
  "schema": "general",
  "domain": "general",
  "model": "string (optional)",
  "temperature": 0.0,
  "max_output_tokens": 1024
}
```

**Response:**
```json
{
  "entities": [...],
  "relationships": [...]
}
```

### POST /api/extract_file

Extract from uploaded files (PDF, DOCX, TXT, HTML).

**Request:** Multipart form data with `file` field

**Response:** Same as `/api/extract`

### POST /api/multi_extract

Multi-model analysis with agreement scoring.

**Request Body:**
```json
{
  "text": "string",
  "language": "fa" | "en",
  "model_first": "string",
  "model_second": "string",
  "model_referee": "string"
}
```

### POST /api/chat

Interactive chat with conversation history.

**Request Body:**
```json
{
  "message": "string",
  "conversation_history": [...]
}
```

### GET /api/schemas

List available extraction schemas.

### GET /api/models

List available Ollama models.

## Interactive Documentation

Visit http://localhost:8000/docs for interactive Swagger UI documentation.

