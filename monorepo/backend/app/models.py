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


# Single model extraction (existing functionality)
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


# Multi-model analysis models
class ModelAnalysis(BaseModel):
	model_name: str
	entities: List[Entity] = Field(default_factory=list)
	relationships: List[Relationship] = Field(default_factory=list)
	confidence_score: Optional[float] = None
	reasoning: Optional[str] = None


class MultiModelRequest(BaseModel):
	text: str
	language: Optional[str] = Field(default="fa", description="fa or en")
	domain: Optional[str] = Field(default="general", description="Domain: general, legal, medical, police")
	
	# Model selections
	model_first: str = Field(..., description="First analysis model")
	model_second: str = Field(..., description="Second analysis model")  
	model_referee: str = Field(..., description="Referee/judge model")
	
	# Optional parameters
	temperature: Optional[float] = None
	max_output_tokens: Optional[int] = None


class MultiModelResponse(BaseModel):
	text: str
	language: str
	domain: str
	
	# Individual model results
	first_analysis: ModelAnalysis
	second_analysis: ModelAnalysis
	
	# Final referee decision
	final_analysis: ModelAnalysis
	
	# Comparison metadata
	agreement_score: Optional[float] = None
	conflicting_entities: List[str] = Field(default_factory=list)
	conflicting_relationships: List[str] = Field(default_factory=list)


class SchemasResponse(BaseModel):
	schemas: List[str]


class DomainsResponse(BaseModel):
	domains: List[str]


# Chat models
class ChatRequest(BaseModel):
	message: str
	language: Optional[str] = Field(default="fa", description="fa or en")
	domain: Optional[str] = Field(default="general", description="Domain: general, legal, medical, police")
	model: Optional[str] = None
	analysisMode: Optional[str] = Field(default="single", description="single or multi")
	model_first: Optional[str] = None
	model_second: Optional[str] = None
	model_referee: Optional[str] = None


class ChatResponse(BaseModel):
	message: str
	analysis: Optional[Dict[str, Any]] = None
	analysisMode: Optional[str] = None
