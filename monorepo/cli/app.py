import os
import json
from pathlib import Path
from typing import Optional

import typer
import requests
from rich import print

# Allow running without backend by using shared module directly
import sys
ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT / "shared"
if str(SHARED) not in sys.path:
	sys.path.insert(0, str(SHARED))
from langextract import run_extraction, generate_html_report  # type: ignore

app = typer.Typer(help="LangExtract CLI")


@app.command()
def extract(
	text: Optional[str] = typer.Option(None, help="Input text. If omitted, read from --file."),
	file: Optional[Path] = typer.Option(None, exists=True, readable=True, help="Path to input text file."),
	language: str = typer.Option("fa", help="fa or en"),
	schema: str = typer.Option("general", help="Schema name"),
	model: Optional[str] = typer.Option(None, help="Ollama model name (default env OLLAMA_MODEL)"),
	use_backend: bool = typer.Option(False, help="Call FastAPI backend instead of local extraction"),
	backend_url: str = typer.Option("http://127.0.0.1:8000", help="Backend base URL"),
	report_out: Optional[Path] = typer.Option(None, help="Output HTML report path"),
):
	"""Extract entities/relationships and optionally save an HTML report."""
	if not text and file:
		text = file.read_text(encoding="utf-8")
	if not text:
		typer.echo("Provide --text or --file")
		raise typer.Exit(code=2)

	if use_backend:
		resp = requests.post(f"{backend_url}/api/extract", json={
			"text": text,
			"language": language,
			"schema": schema,
			"model": model,
		})
		resp.raise_for_status()
		data = resp.json()
	else:
		data = run_extraction(text=text, language=language, schema=schema, model=model)

	print({"entities": len(data.get("entities", [])), "relationships": len(data.get("relationships", []))})

	if report_out:
		html = generate_html_report(source_text=text, extraction=data, language=language, model=model or os.getenv("OLLAMA_MODEL", "gemma3:4b"))
		report_out.write_text(html, encoding="utf-8")
		print(f"[green]Saved report:[/green] {report_out}")

	# stdout JSON
	print(json.dumps(data, ensure_ascii=False))


if __name__ == "__main__":
	app()
