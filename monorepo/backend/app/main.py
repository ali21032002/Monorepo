import os
import sys
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from . import config
from .models import ExtractionRequest, ExtractionResponse, SchemasResponse
from .file_extract import extract_text_from_file

# Add shared package to sys.path
CURRENT_DIR = os.path.dirname(__file__)
MONOREPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
SHARED_DIR = os.path.join(MONOREPO_ROOT, "shared")
if SHARED_DIR not in sys.path:
	sys.path.insert(0, SHARED_DIR)

# Import shared langextract after adjusting path
from langextract import run_extraction, generate_html_report, list_schemas  # type: ignore

app = FastAPI(title="LangExtract Service", version="0.2.0")

app.add_middleware(
	CORSMiddleware,
	allow_origins=config.ALLOW_ORIGINS,
	allow_credentials=config.ALLOW_CREDENTIALS,
	allow_methods=config.ALLOW_METHODS,
	allow_headers=config.ALLOW_HEADERS,
)


@app.get("/api/health")
def health() -> Dict[str, Any]:
	return {
		"status": "ok",
		"ollama_host": config.OLLAMA_HOST,
		"model": config.OLLAMA_MODEL,
	}


@app.get("/api/schemas", response_model=SchemasResponse)
def schemas() -> SchemasResponse:
	return SchemasResponse(schemas=list_schemas())


@app.post("/api/extract", response_model=ExtractionResponse)
def extract(req: ExtractionRequest) -> ExtractionResponse:
	if not req.text or not req.text.strip():
		raise HTTPException(status_code=400, detail="'text' is required")

	language = (req.language or "fa").lower()
	model_name = req.model or config.OLLAMA_MODEL
	temperature = req.temperature if req.temperature is not None else config.TEMPERATURE
	max_output_tokens = req.max_output_tokens if req.max_output_tokens is not None else config.MAX_OUTPUT_TOKENS

	result = run_extraction(
		text=req.text,
		language=language,
		schema=req.schema or "general",
		examples=[e.model_dump() for e in (req.examples or [])],
		model=model_name,
		temperature=temperature,
		max_output_tokens=max_output_tokens,
		request_timeout_seconds=config.REQUEST_TIMEOUT_SECONDS,
		num_ctx=config.NUM_CTX,
		max_input_chars=config.MAX_INPUT_CHARS,
		chunk_overlap_chars=config.CHUNK_OVERLAP_CHARS,
		max_chunks=config.MAX_CHUNKS,
	)

	return ExtractionResponse(
		text=req.text,
		language=language,
		model=model_name,
		entities=result.get("entities", []),
		relationships=result.get("relationships", []),
	)


@app.post("/api/extract_file", response_model=ExtractionResponse)
async def extract_file(
	file: UploadFile = File(...),
	language: str = Form("fa"),
	schema: str = Form("general"),
	model: Optional[str] = Form(None),
	temperature: Optional[float] = Form(None),
	max_output_tokens: Optional[int] = Form(None),
) -> ExtractionResponse:
	data = await file.read()
	text = extract_text_from_file(file.filename, data)
	if not text or not text.strip():
		raise HTTPException(status_code=400, detail="File is empty or unsupported format")

	language = (language or "fa").lower()
	model_name = model or config.OLLAMA_MODEL
	temperature = temperature if temperature is not None else config.TEMPERATURE
	max_output_tokens = max_output_tokens if max_output_tokens is not None else config.MAX_OUTPUT_TOKENS

	result = run_extraction(
		text=text,
		language=language,
		schema=schema or "general",
		examples=[],
		model=model_name,
		temperature=temperature,
		max_output_tokens=max_output_tokens,
		request_timeout_seconds=config.REQUEST_TIMEOUT_SECONDS,
		num_ctx=config.NUM_CTX,
		max_input_chars=config.MAX_INPUT_CHARS,
		chunk_overlap_chars=config.CHUNK_OVERLAP_CHARS,
		max_chunks=config.MAX_CHUNKS,
	)

	return ExtractionResponse(
		text=text,
		language=language,
		model=model_name,
		entities=result.get("entities", []),
		relationships=result.get("relationships", []),
	)


@app.post("/api/report", response_class=HTMLResponse)
def report(req: ExtractionRequest) -> HTMLResponse:
	if not req.text or not req.text.strip():
		raise HTTPException(status_code=400, detail="'text' is required")

	language = (req.language or "fa").lower()
	model_name = req.model or config.OLLAMA_MODEL
	temperature = req.temperature if req.temperature is not None else config.TEMPERATURE
	max_output_tokens = req.max_output_tokens if req.max_output_tokens is not None else config.MAX_OUTPUT_TOKENS

	result = run_extraction(
		text=req.text,
		language=language,
		schema=req.schema or "general",
		examples=[e.model_dump() for e in (req.examples or [])],
		model=model_name,
		temperature=temperature,
		max_output_tokens=max_output_tokens,
		request_timeout_seconds=config.REQUEST_TIMEOUT_SECONDS,
		num_ctx=config.NUM_CTX,
		max_input_chars=config.MAX_INPUT_CHARS,
		chunk_overlap_chars=config.CHUNK_OVERLAP_CHARS,
		max_chunks=config.MAX_CHUNKS,
	)

	html = generate_html_report(source_text=req.text, extraction=result, language=language, model=model_name)
	return HTMLResponse(content=html)
