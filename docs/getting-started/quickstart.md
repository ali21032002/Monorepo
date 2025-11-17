# Quick Start

Get started with Mentora in minutes!

## Starting the Services

### 1. Start Backend Service

```powershell
cd monorepo\backend
. .venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Start Frontend (New Terminal)

```powershell
cd monorepo\frontend
npm run dev
```

Open the printed localhost URL (default `http://localhost:5173`).

### 3. Start Speech-to-Text Service (Optional)

```powershell
cd monorepo\speechToText
. .venv\Scripts\Activate.ps1
python app.py
```

## Using the CLI

Extract entities from text:

```powershell
cd monorepo\cli
. .venv\Scripts\Activate.ps1
python app.py extract --text "علی در تهران زندگی می‌کند." --language fa --report-out report.html
```

## API Usage Example

### Python

```python
import requests

response = requests.post(
    "http://localhost:8000/api/extract",
    json={
        "text": "علی در تهران زندگی می‌کند.",
        "language": "fa",
        "schema": "general"
    }
)
print(response.json())
```

### JavaScript/TypeScript

```typescript
const response = await fetch('http://localhost:8000/api/extract', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    text: 'علی در تهران زندگی می‌کند.',
    language: 'fa',
    schema: 'general'
  })
});
const data = await response.json();
console.log(data);
```

## Next Steps

- Explore the [API Reference](../api/backend.md)
- Check out [Examples](../examples.md)
- Learn about the [Architecture](../architecture.md)

