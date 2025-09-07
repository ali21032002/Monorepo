# LangExtract Backend

Run local FastAPI service that calls Ollama Gemma3:4b.

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
