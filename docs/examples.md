# Examples

This page contains practical examples of using Mentora.

## Basic Extraction

### Python

```python
from langextract import run_extraction

result = run_extraction(
    text="علی در تهران زندگی می‌کند و در شرکت فناوری کار می‌کند.",
    language="fa",
    schema="general"
)

for entity in result["entities"]:
    print(f"{entity['name']} ({entity['type']})")

for rel in result["relationships"]:
    print(f"{rel['source_entity_id']} -> {rel['target_entity_id']}: {rel['type']}")
```

### API Call

```python
import requests

response = requests.post(
    "http://localhost:8000/api/extract",
    json={
        "text": "علی در تهران زندگی می‌کند.",
        "language": "fa"
    }
)
data = response.json()
print(data)
```

## Multi-Model Analysis

```python
from langextract import run_multi_model_analysis

result = run_multi_model_analysis(
    text="علی در تهران زندگی می‌کند.",
    language="fa",
    model_first="gemma3:4b",
    model_second="llama3:8b",
    model_referee="gemma3:4b"
)

print(f"Agreement Score: {result['agreement_score']}")
print(f"Conflicting Entities: {result['conflicting_entities']}")
```

## File Processing

```python
import requests

with open("document.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/extract_file",
        files={"file": f},
        data={"language": "fa", "schema": "general"}
    )
    result = response.json()
    print(result)
```

## Speech-to-Text

```python
import requests

with open("audio.wav", "rb") as f:
    response = requests.post(
        "http://localhost:8001/transcribe-hybrid",
        files={"audio": f}
    )
    result = response.json()
    print(result["text"])
```

