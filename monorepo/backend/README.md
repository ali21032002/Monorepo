# LangExtract Backend

Run local FastAPI service that calls Ollama Gemma3:4b with comprehensive Swagger API documentation.

## Setup (Windows PowerShell)

```
cd monorepo\backend
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:OLLAMA_HOST = "http://127.0.0.1:11434"
$env:OLLAMA_MODEL = "gemma3:4b"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Ollama must be running and model pulled:

```
ollama pull gemma3:4b
```

## 📚 API Documentation (Swagger)

The service includes comprehensive Swagger documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### 🔧 Main Endpoints

#### Text Analysis
- `POST /api/extract` - Extract entities and relationships from text
- `POST /api/extract_file` - Extract from uploaded files (PDF, DOCX, TXT)
- `POST /api/multi_extract` - Multi-model analysis with agreement scoring
- `POST /api/report` - Generate HTML report

#### Chat & Interaction
- `POST /api/chat` - Interactive chat with conversation history
- `POST /api/chat-with-images` - Chat with image support (coming soon)

#### Speech Integration
- `POST /api/speech-to-text` - Convert speech to text
- `POST /api/chat-speech-to-text` - Speech-to-text optimized for chat

#### Configuration & Info
- `GET /api/health` - Service health check
- `GET /api/schemas` - List available extraction schemas
- `GET /api/domains` - List available analysis domains
- `GET /api/models` - List available Ollama models
- `GET /api/config/tokens` - Get current token configuration

#### Elasticsearch Integration
- `GET /api/es/health` - Elasticsearch connection status
- `GET /api/es/indices` - List ES indices
- `GET /api/reports/search` - Search chat history
- `GET /api/reports/overview` - Reports overview

### 🌐 Features

- **Multi-language Support**: Persian and English
- **Multi-model Analysis**: Compare results from different models
- **Conversation History**: Maintain context across chat sessions
- **File Processing**: Support for various document formats
- **Speech Integration**: Voice input support
- **Real-time Configuration**: Dynamic model switching
- **Comprehensive Logging**: Elasticsearch integration for analytics

### 📝 Example Usage

#### Extract Entities from Text
```bash
curl -X POST "http://localhost:8000/api/extract" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "علی در تهران زندگی می‌کند و در شرکت فناوری کار می‌کند.",
    "language": "fa",
    "schema_name": "general"
  }'
```

#### Multi-model Analysis
```bash
curl -X POST "http://localhost:8000/api/multi_extract" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "محمد دانشجوی دانشگاه تهران است.",
    "language": "fa",
    "model_first": "gemma3:4b",
    "model_second": "qwen2.5:7b",
    "model_referee": "llama3:8b"
  }'
```

#### Chat with History
```bash
curl -X POST "http://localhost:8000/api/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "سلام، چطور می‌تونم کمکتون کنم؟",
    "language": "fa",
    "domain": "general",
    "message_history": []
  }'
```
