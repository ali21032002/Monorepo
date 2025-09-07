# LangExtract Local (Ollama Gemma3:4b)

Use LangExtract to extract entities and relationships from Persian or English text with a fully local LLM (Ollama Gemma3:4b).

## Features
- Use of LangExtract for entity and relationship extraction (fa/en)
- Integration with Ollama’s Gemma 3:4b local LLM
- Few-shot examples for improved extraction accuracy
- Example CLI and HTML report generation
- React UI to visualize results

## Monorepo Structure
```
monorepo/
  backend/      # FastAPI service
  frontend/     # React + Vite app
  cli/          # Typer CLI + pytest smoke test
  shared/       # LangExtract shared Python package
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

4) CLI (optional)
```
cd monorepo\cli
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py extract --text "علی در تهران زندگی می‌کند." --language fa --report-out report.html
```

## Notes
- Ensure Ollama app/service is running. Default host: `http://127.0.0.1:11434`.
- You can change the model by setting `OLLAMA_MODEL` or choosing in the UI.
