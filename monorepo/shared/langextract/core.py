import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from .prompts import build_system_prompt, build_user_prompt
from .schemas import ensure_extraction_shape
from .ollama_backend import chat_json


def _extract_first_json_block(text: str) -> str:
	match = re.search(r"\{[\s\S]*\}\s*$", text.strip())
	if match:
		return match.group(0)
	# Fallback: try to find the first and last curly brace
	start = text.find("{")
	end = text.rfind("}")
	if start != -1 and end != -1 and end > start:
		return text[start : end + 1]
	return "{}"


def _to_json(content: str) -> Dict[str, Any]:
	try:
		return json.loads(content)
	except json.JSONDecodeError:
		block = _extract_first_json_block(content)
		try:
			return json.loads(block)
		except Exception:
			return {}


def run_extraction(
	*,
	text: str,
	language: str = "fa",
	schema: str = "general",
	examples: Optional[List[Dict[str, Any]]] = None,
	model: Optional[str] = None,
	temperature: float = 0.0,
	max_output_tokens: int = 1024,
	request_timeout_seconds: Optional[int] = None,
	num_ctx: Optional[int] = None,
	max_input_chars: Optional[int] = None,
	chunk_overlap_chars: Optional[int] = None,
	max_chunks: Optional[int] = None,
) -> Dict[str, Any]:
	model_name = model or os.getenv("OLLAMA_MODEL", "gemma3:4b")

	def _call_model(src_text: str) -> Dict[str, Any]:
		system_prompt = build_system_prompt(language=language, schema_name=schema)
		user_prompt = build_user_prompt(text=src_text, language=language, examples=examples or [])
		content = chat_json(
			system_prompt=system_prompt,
			user_prompt=user_prompt,
			model=model_name,
			temperature=temperature,
			max_output_tokens=max_output_tokens,
			request_timeout_seconds=request_timeout_seconds,
			num_ctx=num_ctx,
		)
		return ensure_extraction_shape(_to_json(content))

	# Resolve chunking parameters
	max_in = int(max_input_chars) if max_input_chars is not None else int(os.getenv("MAX_INPUT_CHARS", "12000"))
	overlap = int(chunk_overlap_chars) if chunk_overlap_chars is not None else int(os.getenv("CHUNK_OVERLAP_CHARS", "200"))
	max_parts = int(max_chunks) if max_chunks is not None else int(os.getenv("MAX_CHUNKS", "8"))

	if len(text) <= max_in:
		return _call_model(text)

	# Chunk long input by character length with an overlap for context preservation
	def _chunk_text(t: str, size: int, ov: int, limit: int) -> List[str]:
		chunks: List[str] = []
		start = 0
		while start < len(t) and len(chunks) < limit:
			end = min(start + size, len(t))
			chunks.append(t[start:end])
			if end == len(t):
				break
			start = max(end - ov, start + 1)
		return chunks

	parts = _chunk_text(text, max_in, overlap, max_parts)
	all_entities: List[Dict[str, Any]] = []
	all_relationships: List[Dict[str, Any]] = []

	# Dedup helpers
	def _entity_key(e: Dict[str, Any]) -> Tuple[str, str]:
		return (str(e.get("name", "")).strip().lower(), str(e.get("type", "")).strip().lower())

	def _rel_key(r: Dict[str, Any]) -> Tuple[str, str, str]:
		return (
			str(r.get("source_entity_id", "")),
			str(r.get("target_entity_id", "")),
			str(r.get("type", "")),
		)

	seen_entities: set = set()
	seen_rels: set = set()

	for p in parts:
		res = _call_model(p)
		for e in res.get("entities", []):
			k = _entity_key(e)
			if k not in seen_entities:
				seen_entities.add(k)
				all_entities.append(e)
		for r in res.get("relationships", []):
			k2 = _rel_key(r)
			if k2 not in seen_rels:
				seen_rels.add(k2)
				all_relationships.append(r)

	return {"entities": all_entities, "relationships": all_relationships}
