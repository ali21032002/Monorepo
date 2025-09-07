import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from .prompts import build_system_prompt, build_user_prompt, build_referee_prompt
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
	domain: str = "general",
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
		system_prompt = build_system_prompt(language=language, schema_name=schema, domain=domain)
		user_prompt = build_user_prompt(text=src_text, language=language, examples=examples or [], domain=domain)
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


def run_multi_model_analysis(
	*,
	text: str,
	language: str = "fa",
	domain: str = "general",
	model_first: str,
	model_second: str,
	model_referee: str,
	temperature: float = 0.0,
	max_output_tokens: int = 1024,
	request_timeout_seconds: Optional[int] = None,
	num_ctx: Optional[int] = None,
) -> Dict[str, Any]:
	"""
	Run multi-model analysis with two models + referee
	"""
	
	def _analyze_with_model(model_name: str, src_text: str) -> Dict[str, Any]:
		"""Run single model analysis"""
		system_prompt = build_system_prompt(language=language, schema_name="general", domain=domain)
		user_prompt = build_user_prompt(text=src_text, language=language, examples=[], domain=domain)
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
	
	def _calculate_agreement_score(analysis1: Dict[str, Any], analysis2: Dict[str, Any]) -> float:
		"""Calculate agreement score between two analyses"""
		entities1 = set((e.get("name", "").lower(), e.get("type", "").lower()) for e in analysis1.get("entities", []))
		entities2 = set((e.get("name", "").lower(), e.get("type", "").lower()) for e in analysis2.get("entities", []))
		
		if not entities1 and not entities2:
			return 1.0
		if not entities1 or not entities2:
			return 0.0
			
		intersection = len(entities1.intersection(entities2))
		union = len(entities1.union(entities2))
		return intersection / union if union > 0 else 0.0
	
	def _find_conflicts(analysis1: Dict[str, Any], analysis2: Dict[str, Any]) -> Tuple[List[str], List[str]]:
		"""Find conflicting entities and relationships"""
		entities1 = {(e.get("name", "").lower(), e.get("type", "").lower()) for e in analysis1.get("entities", [])}
		entities2 = {(e.get("name", "").lower(), e.get("type", "").lower()) for e in analysis2.get("entities", [])}
		
		conflicting_entities = []
		for e1 in analysis1.get("entities", []):
			name_type = (e1.get("name", "").lower(), e1.get("type", "").lower())
			if name_type not in entities2:
				conflicting_entities.append(f"{e1.get('name')} ({e1.get('type')})")
		
		for e2 in analysis2.get("entities", []):
			name_type = (e2.get("name", "").lower(), e2.get("type", "").lower())
			if name_type not in entities1:
				conflicting_entities.append(f"{e2.get('name')} ({e2.get('type')})")
		
		# Simple relationship conflict detection
		rels1 = {(r.get("source_entity_id", ""), r.get("target_entity_id", ""), r.get("type", "")) for r in analysis1.get("relationships", [])}
		rels2 = {(r.get("source_entity_id", ""), r.get("target_entity_id", ""), r.get("type", "")) for r in analysis2.get("relationships", [])}
		
		conflicting_relationships = []
		all_rels = rels1.union(rels2)
		for rel in all_rels:
			if rel in rels1 and rel not in rels2:
				conflicting_relationships.append(f"{rel[0]} -> {rel[1]} ({rel[2]})")
			elif rel in rels2 and rel not in rels1:
				conflicting_relationships.append(f"{rel[0]} -> {rel[1]} ({rel[2]})")
		
		return conflicting_entities, conflicting_relationships
	
	# Step 1: Run first two models
	print(f"Running first model analysis: {model_first}")
	first_analysis = _analyze_with_model(model_first, text)
	
	print(f"Running second model analysis: {model_second}")
	second_analysis = _analyze_with_model(model_second, text)
	
	# Step 2: Calculate agreement and conflicts
	agreement_score = _calculate_agreement_score(first_analysis, second_analysis)
	conflicting_entities, conflicting_relationships = _find_conflicts(first_analysis, second_analysis)
	
	# Step 3: Run referee model
	print(f"Running referee model: {model_referee}")
	referee_prompt = build_referee_prompt(
		text=text,
		language=language,
		first_analysis=first_analysis,
		second_analysis=second_analysis,
		domain=domain
	)
	
	referee_content = chat_json(
		system_prompt=build_system_prompt(language=language, schema_name="general", domain=domain),
		user_prompt=referee_prompt,
		model=model_referee,
		temperature=temperature,
		max_output_tokens=max_output_tokens,
		request_timeout_seconds=request_timeout_seconds,
		num_ctx=num_ctx,
	)
	final_analysis = ensure_extraction_shape(_to_json(referee_content))
	
	return {
		"text": text,
		"language": language,
		"domain": domain,
		"first_analysis": {
			"model_name": model_first,
			"entities": first_analysis.get("entities", []),
			"relationships": first_analysis.get("relationships", []),
		},
		"second_analysis": {
			"model_name": model_second,
			"entities": second_analysis.get("entities", []),
			"relationships": second_analysis.get("relationships", []),
		},
		"final_analysis": {
			"model_name": model_referee,
			"entities": final_analysis.get("entities", []),
			"relationships": final_analysis.get("relationships", []),
		},
		"agreement_score": agreement_score,
		"conflicting_entities": conflicting_entities,
		"conflicting_relationships": conflicting_relationships,
	}
