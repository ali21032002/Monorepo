# Installation

This guide will help you install and set up the Mentora system.

## Prerequisites

- Python 3.8 or higher
- Node.js 16 or higher (for frontend)
- Ollama installed and running locally
- Windows PowerShell (for Windows users)

## Step 1: Install Ollama

1. Download and install Ollama from [ollama.ai](https://ollama.ai)
2. Start Ollama service:
   ```powershell
   ollama serve
   ```
3. Pull the required model:
   ```powershell
   ollama pull gemma3:4b
   ```

## Step 2: Backend Setup

```powershell
cd monorepo\backend
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Set environment variables:
```powershell
$env:OLLAMA_HOST = "http://127.0.0.1:11434"
$env:OLLAMA_MODEL = "gemma3:4b"
```

## Step 3: Frontend Setup

```powershell
cd monorepo\frontend
npm install
```

## Step 4: Speech-to-Text Service (Optional)

```powershell
cd monorepo\speechToText
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Step 5: CLI Setup (Optional)

```powershell
cd monorepo\cli
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Verification

After installation, you can verify the setup by running the services and checking the Swagger documentation at:
- Backend: http://localhost:8000/docs
- Speech-to-Text: http://localhost:8001/docs

