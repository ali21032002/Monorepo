from typing import Any, Dict, List

from .schemas import get_schema_instructions


FEW_SHOT_FA: List[Dict[str, Any]] = [
	{
		"text": "علی در تهران زندگی می‌کند و در شرکت دیجی‌کالا کار می‌کند.",
		"entities": [
			{"name": "علی", "type": "PERSON"},
			{"name": "تهران", "type": "LOCATION"},
			{"name": "دیجی‌کالا", "type": "ORGANIZATION"},
		],
		"relationships": [
			{"source_entity_id": "PERSON:علی", "target_entity_id": "ORGANIZATION:دیجی‌کالا", "type": "EMPLOYED_AT"},
			{"source_entity_id": "PERSON:علی", "target_entity_id": "LOCATION:تهران", "type": "LIVES_IN"},
		],
	},
]

FEW_SHOT_EN: List[Dict[str, Any]] = [
	{
		"text": "Sara moved to Berlin in 2019 and works at Google.",
		"entities": [
			{"name": "Sara", "type": "PERSON"},
			{"name": "Berlin", "type": "LOCATION"},
			{"name": "2019", "type": "DATE"},
			{"name": "Google", "type": "ORGANIZATION"},
		],
		"relationships": [
			{"source_entity_id": "PERSON:Sara", "target_entity_id": "LOCATION:Berlin", "type": "MOVED_TO"},
			{"source_entity_id": "PERSON:Sara", "target_entity_id": "ORGANIZATION:Google", "type": "EMPLOYED_AT"},
		],
	},
]


def build_system_prompt(*, language: str, schema_name: str) -> str:
	schema_instruction = get_schema_instructions(schema_name)
	return (
		"You are a precise information extraction engine. "
		"Output only minified JSON that conforms to the schema. "
		"Do not include any explanations or extra text.\n\n" + schema_instruction
	)


def build_user_prompt(*, text: str, language: str, examples: List[Dict[str, Any]]) -> str:
	few_shots = examples
	if not few_shots:
		few_shots = FEW_SHOT_FA if language.lower().startswith("fa") else FEW_SHOT_EN

	shots_str_items: List[str] = []
	for ex in few_shots:
		shots_str_items.append(
			f"TEXT:\n{ex['text']}\nJSON:\n" + "{" + f"\"entities\": {ex.get('entities', [])}, \"relationships\": {ex.get('relationships', [])}" + "}"
		)
	shots_str = "\n\n".join(shots_str_items)

	return (
		f"LANGUAGE: {language}\n"
		"Return JSON with keys: entities, relationships. Entities need name and type.\n"
		"If unsure, leave arrays empty.\n\n"
		f"FEW-SHOTS:\n{shots_str}\n\n"
		f"NOW EXTRACT FROM THIS TEXT:\n{text}\n"
	)
