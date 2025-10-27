# LangExtract Local (Ollama Gemma3:4b)

Use LangExtract to extract entities and relationships from Persian or English text with a fully local LLM (Ollama Gemma3:4b).

## Features
- Use of LangExtract for entity and relationship extraction (fa/en)
- Integration with Ollama's Gemma 3:4b local LLM
- Few-shot examples for improved extraction accuracy
- Example CLI and HTML report generation
- React UI to visualize results
- **Swagger API Documentation** for all microservices
- **Speech-to-Text Service** with hybrid Persian models
- **Multi-model analysis** with agreement scoring

## Monorepo Structure
```
monorepo/
  backend/      # FastAPI service (Port 8000)
  frontend/     # React + Vite app (Port 5173)
  cli/          # Typer CLI + pytest smoke test
  shared/       # LangExtract shared Python package
  speechToText/ # Speech-to-Text service (Port 8001)
examples/
```

## Quickstart (Windows PowerShell)

1) Start Ollama locally and pull model:
```
ollama serve
ollama pull gemma3:4b
```

2) Backend
```
cd monorepo\backend
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:OLLAMA_HOST = "http://127.0.0.1:11434"
$env:OLLAMA_MODEL = "gemma3:4b"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

3) Frontend (new terminal)
```
cd monorepo\frontend
npm install
npm run dev
```
Open the printed localhost URL (default `http://localhost:5173`).

4) Speech-to-Text Service (optional)
```
cd monorepo\speechToText
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

5) CLI (optional)
```
cd monorepo\cli
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py extract --text "علی در تهران زندگی می‌کند." --language fa --report-out report.html
```

## 📚 API Documentation (Swagger)

All microservices include comprehensive Swagger documentation:

### 🔧 Backend Service (Port 8000)
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

**Key Endpoints:**
- `POST /api/extract` - Extract entities and relationships from text
- `POST /api/extract_file` - Extract from uploaded files
- `POST /api/multi_extract` - Multi-model analysis with agreement scoring
- `POST /api/chat` - Interactive chat with conversation history
- `POST /api/speech-to-text` - Convert speech to text
- `GET /api/schemas` - List available extraction schemas
- `GET /api/models` - List available Ollama models

### 🎤 Speech-to-Text Service (Port 8001)
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc
- **OpenAPI JSON**: http://localhost:8001/openapi.json

**Key Endpoints:**
- `POST /transcribe` - Basic speech-to-text conversion
- `POST /transcribe-chat` - Optimized for chat interface
- `POST /transcribe-hybrid` - Hybrid Persian models for maximum accuracy
- `GET /models` - List available speech models
- `GET /health` - Service health check
- `GET /diagnose` - System environment diagnostics

### 🌐 Frontend Integration
The React frontend automatically integrates with both services:
- Backend API calls for text analysis and chat
- Speech-to-text integration for voice input
- Real-time model switching and configuration

### 📖 Detailed Examples
For comprehensive API usage examples, see [SWAGGER_EXAMPLES.md](SWAGGER_EXAMPLES.md) which includes:
- Complete request/response examples
- JavaScript/TypeScript integration code
- Python usage examples
- Error handling patterns
- Best practices and tips

## Notes
- Ensure Ollama app/service is running. Default host: `http://127.0.0.1:11434`.
- You can change the model by setting `OLLAMA_MODEL` or choosing in the UI.
- All API endpoints support both Persian and English languages.
- Swagger documentation includes detailed parameter descriptions and examples.
