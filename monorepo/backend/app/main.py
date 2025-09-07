import os
import sys
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from . import config
from .models import ExtractionRequest, ExtractionResponse, SchemasResponse, MultiModelRequest, MultiModelResponse, DomainsResponse, ModelAnalysis
from .file_extract import extract_text_from_file

# Add shared package to sys.path
CURRENT_DIR = os.path.dirname(__file__)
MONOREPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
SHARED_DIR = os.path.join(MONOREPO_ROOT, "shared")
if SHARED_DIR not in sys.path:
	sys.path.insert(0, SHARED_DIR)

# Import shared langextract after adjusting path
from langextract import run_extraction, run_multi_model_analysis, generate_html_report, list_schemas  # type: ignore

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


@app.get("/api/domains", response_model=DomainsResponse)
def domains() -> DomainsResponse:
	return DomainsResponse(domains=["general", "legal", "medical", "police"])


@app.get("/api/models")
def get_ollama_models() -> Dict[str, Any]:
	"""Get list of available Ollama models"""
	try:
		import subprocess
		import json
		
		# Try ollama list with JSON first
		result = subprocess.run(
			["ollama", "list", "--json"], 
			capture_output=True, 
			text=True, 
			timeout=10
		)
		
		if result.returncode == 0:
			try:
				models_data = json.loads(result.stdout)
				models = []
				
				# Extract model names
				if "models" in models_data:
					for model in models_data["models"]:
						if "name" in model:
							models.append(model["name"])
				
				return {
					"status": "success",
					"models": models,
					"count": len(models)
				}
			except json.JSONDecodeError:
				pass  # Fall through to text parsing
		
		# Try regular ollama list (text format)
		result = subprocess.run(
			["ollama", "list"], 
			capture_output=True, 
			text=True, 
			timeout=10
		)
		
		if result.returncode == 0:
			# Parse text output
			lines = result.stdout.strip().split('\n')
			models = []
			for line in lines[1:]:  # Skip header line
				if line.strip():
					parts = line.split()
					if parts:
						model_name = parts[0]  # First column is model name
						# Filter out system models and keep only main models
						if not model_name.startswith('.') and ':' in model_name:
							models.append(model_name)
			
			return {
				"status": "success", 
				"models": models,
				"count": len(models)
			}
		else:
			# Return some default models if ollama command fails
			default_models = ["gemma3:4b", "qwen2.5:7b", "gemma2:9b", "llama3:8b"]
			return {
				"status": "fallback",
				"models": default_models,
				"count": len(default_models),
				"error": "Could not connect to Ollama, showing common models"
			}
			
	except Exception as e:
		# Return fallback models in case of any error
		default_models = ["gemma3:4b", "qwen2.5:7b", "gemma2:9b", "llama3:8b"]
		return {
			"status": "error",
			"models": default_models,
			"count": len(default_models),
			"error": str(e)
		}


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
		domain="general",  # Add domain parameter
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
		domain="general",  # Add domain parameter
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
		domain="general",  # Add domain parameter
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


@app.post("/api/multi_extract", response_model=MultiModelResponse)
def multi_extract(req: MultiModelRequest) -> MultiModelResponse:
	if not req.text or not req.text.strip():
		raise HTTPException(status_code=400, detail="'text' is required")

	language = (req.language or "fa").lower()
	domain = req.domain or "general"
	temperature = req.temperature if req.temperature is not None else config.TEMPERATURE
	max_output_tokens = req.max_output_tokens if req.max_output_tokens is not None else config.MAX_OUTPUT_TOKENS

	try:
		result = run_multi_model_analysis(
			text=req.text,
			language=language,
			domain=domain,
			model_first=req.model_first,
			model_second=req.model_second,
			model_referee=req.model_referee,
			temperature=temperature,
			max_output_tokens=max_output_tokens,
			request_timeout_seconds=config.REQUEST_TIMEOUT_SECONDS,
			num_ctx=config.NUM_CTX,
		)

		return MultiModelResponse(
			text=result["text"],
			language=result["language"],
			domain=result["domain"],
			first_analysis=ModelAnalysis(**result["first_analysis"]),
			second_analysis=ModelAnalysis(**result["second_analysis"]),
			final_analysis=ModelAnalysis(**result["final_analysis"]),
			agreement_score=result["agreement_score"],
			conflicting_entities=result["conflicting_entities"],
			conflicting_relationships=result["conflicting_relationships"],
		)
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
