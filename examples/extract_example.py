import os
from pathlib import Path
import requests

BACKEND = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
TEXT = "علی در تهران زندگی می‌کند و در شرکت دیجی‌کالا کار می‌کند."

print("Posting to /api/extract ...")
r = requests.post(f"{BACKEND}/api/extract", json={
	"text": TEXT,
	"language": "fa",
	"schema": "general",
})
r.raise_for_status()
print("JSON:", r.json())

print("Posting to /api/report ...")
report = requests.post(f"{BACKEND}/api/report", json={
	"text": TEXT,
	"language": "fa",
	"schema": "general",
})
report.raise_for_status()
out = Path("report_example.html")
out.write_text(report.text, encoding="utf-8")
print("Saved:", out.resolve())
