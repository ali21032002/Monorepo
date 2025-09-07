from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Entity(BaseModel):
	id: Optional[str] = None
	name: str
	type: str = Field(..., description="Entity type such as PERSON, ORG, LOCATION, DATE, etc.")	
	start_index: Optional[int] = None
	end_index: Optional[int] = None
	attributes: Dict[str, Any] = Field(default_factory=dict)


class Relationship(BaseModel):
	id: Optional[str] = None
	source_entity_id: str
	target_entity_id: str
	type: str
	attributes: Dict[str, Any] = Field(default_factory=dict)


class FewShotExample(BaseModel):
	text: str
	entities: List[Entity] = Field(default_factory=list)
	relationships: List[Relationship] = Field(default_factory=list)


class ExtractionRequest(BaseModel):
	text: str
	language: Optional[str] = Field(default=None, description="fa or en")
	schema: Optional[str] = Field(default="general")
	examples: Optional[List[FewShotExample]] = None
	model: Optional[str] = None
	temperature: Optional[float] = None
	max_output_tokens: Optional[int] = None


class ExtractionResponse(BaseModel):
	text: str
	language: str
	model: str
	entities: List[Entity] = Field(default_factory=list)
	relationships: List[Relationship] = Field(default_factory=list)


class SchemasResponse(BaseModel):
	schemas: List[str]
