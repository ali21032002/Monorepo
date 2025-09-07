from typing import Any, Dict, List

_SCHEMAS: Dict[str, str] = {
	"general": (
		"Schema: {\n"
		"  \"entities\": [ { \"name\": string, \"type\": string, \"start_index\"?: int, \"end_index\"?: int, \"attributes\"?: object } ],\n"
		"  \"relationships\": [ { \"source_entity_id\": string, \"target_entity_id\": string, \"type\": string, \"attributes\"?: object } ]\n"
		"}\n"
	),
}


def get_schema_instructions(name: str) -> str:
	return _SCHEMAS.get(name, _SCHEMAS["general"])


def list_schemas() -> List[str]:
	return list(_SCHEMAS.keys())


def ensure_extraction_shape(data: Dict[str, Any]) -> Dict[str, Any]:
	entities = data.get("entities")
	relationships = data.get("relationships")
	if not isinstance(entities, list):
		entities = []
	if not isinstance(relationships, list):
		relationships = []
	# Normalize entity fields
	norm_entities: List[Dict[str, Any]] = []
	for e in entities:
		if not isinstance(e, dict):
			continue
		name = e.get("name")
		type_ = e.get("type")
		if not name or not type_:
			continue
		item = {
			"id": e.get("id"),
			"name": str(name),
			"type": str(type_),
			"start_index": e.get("start_index"),
			"end_index": e.get("end_index"),
			"attributes": e.get("attributes") or {},
		}
		norm_entities.append(item)

	norm_relationships: List[Dict[str, Any]] = []
	for r in relationships:
		if not isinstance(r, dict):
			continue
		se = r.get("source_entity_id")
		te = r.get("target_entity_id")
		type_ = r.get("type")
		if not se or not te or not type_:
			continue
		item = {
			"id": r.get("id"),
			"source_entity_id": str(se),
			"target_entity_id": str(te),
			"type": str(type_),
			"attributes": r.get("attributes") or {},
		}
		norm_relationships.append(item)

	return {"entities": norm_entities, "relationships": norm_relationships}
