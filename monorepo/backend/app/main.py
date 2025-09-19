import os
import sys
import httpx
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from . import config
from .models import ExtractionRequest, ExtractionResponse, SchemasResponse, MultiModelRequest, MultiModelResponse, DomainsResponse, ModelAnalysis, ChatRequest, ChatResponse, SpeechToTextRequest, SpeechToTextResponse, ChartData, ChartDataset
from .file_extract import extract_text_from_file

# Add shared package to sys.path
CURRENT_DIR = os.path.dirname(__file__)
MONOREPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
SHARED_DIR = os.path.join(MONOREPO_ROOT, "shared")
if SHARED_DIR not in sys.path:
	sys.path.insert(0, SHARED_DIR)

# Import shared langextract after adjusting path
from langextract import run_extraction, run_multi_model_analysis, generate_html_report, list_schemas  # type: ignore
from langextract.ollama_backend import chat_conversational  # type: ignore

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


@app.get("/api/speech-models")
def get_speech_models() -> Dict[str, Any]:
	"""Get information about available speech-to-text models"""
	try:
		with httpx.Client(timeout=10.0) as client:
			response = client.get("http://localhost:8001/models")
			
			if response.status_code == 200:
				return response.json()
			else:
				return {
					"status": "error",
					"error": f"Speech service returned {response.status_code}",
					"models": {},
					"hybrid_mode": "unavailable"
				}
	except Exception as e:
		return {
			"status": "error",
			"error": f"Speech service unavailable: {str(e)}",
			"models": {},
			"hybrid_mode": "unavailable"
		}

@app.get("/api/chat-speech-status")
def get_chat_speech_status() -> Dict[str, Any]:
	"""Get speech-to-text status specifically for chatbot"""
	try:
		with httpx.Client(timeout=10.0) as client:
			# Check both hybrid and regular endpoints
			hybrid_response = client.get("http://localhost:8001/health")
			
			if hybrid_response.status_code == 200:
				health_data = hybrid_response.json()
				return {
					"status": "ok",
					"hybrid_available": health_data.get("hybrid_mode") == "available",
					"whisper_available": health_data.get("whisper_available", False),
					"huggingface_available": health_data.get("huggingface_available", False),
					"persian_models": health_data.get("persian_models", {}),
					"recommended_endpoint": "/api/chat-speech-to-text",
					"note": "Chatbot optimized for Persian hybrid speech recognition"
				}
			else:
				return {
					"status": "error",
					"hybrid_available": False,
					"whisper_available": False,
					"error": f"Speech service returned {hybrid_response.status_code}"
				}
	except Exception as e:
		return {
			"status": "error",
			"hybrid_available": False,
			"whisper_available": False,
			"error": f"Speech service unavailable: {str(e)}"
		}

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

	# Check if user is asking about the AI assistant
	ai_question_keywords = [
		'تو کی هستی', 'تو کجا توسعه پیدا کردی', 'چه کسی نوشته ات', 'چه کسی توسعه داده ات', 'علی سلیمی کیه؟',
		'کجا آموزش دیده ای', 'توسعه دهنده تو کیست', 'نویسنده تو کیست', 'چه کسی تو را ساخته','نویسنده تو چه کسی است' ,
		'who are you', 'who created you', 'who developed you', 'who wrote you',
		'where were you developed', 'where were you trained'
	]
	is_ai_question = any(keyword in req.text.lower() for keyword in ai_question_keywords)
	
	if is_ai_question:
		ai_response = """من دستیار هوش مصنوعی هستم که در مرکز مدیریت و تحلیل داده فراجا و اداره مهندسی داده توسعه داده شده و آموزش دیده‌ام. توسعه‌دهنده من، سرهنگ مهندس علی سلیمی است و آماده‌ام تا شما را راهنمایی کنم."""
		return ExtractionResponse(
			text=req.text,
			language=language,
			model=model_name,
			entities=[{
				"text": ai_response,
				"label": "AI_Response",
				"start": 0,
				"end": len(ai_response),
				"confidence": 1.0
			}],
			relationships=[]
		)

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

	# Check if user is asking about the AI assistant
	ai_question_keywords = [
		'تو کی هستی', 'تو کجا توسعه پیدا کردی', 'چه کسی نوشته ات', 'چه کسی توسعه داده ات',
		'کجا آموزش دیده ای', 'توسعه دهنده تو کیست', 'نویسنده تو کیست', 'چه کسی تو را ساخته',
		'who are you', 'who created you', 'who developed you', 'who wrote you',
		'where were you developed', 'where were you trained'
	]
	is_ai_question = any(keyword in text.lower() for keyword in ai_question_keywords)
	
	if is_ai_question:
		ai_response = """من دستیار هوش مصنوعی هستم که در مرکز مدیریت و تحلیل داده فراجا و اداره مهندسی داده توسعه داده شده و آموزش دیده‌ام. توسعه‌دهنده من، سرهنگ مهندس علی سلیمی است و آماده‌ام تا شما را راهنمایی کنم."""
		return ExtractionResponse(
			text=text,
			language=language,
			model=model_name,
			entities=[{
				"text": ai_response,
				"label": "AI_Response",
				"start": 0,
				"end": len(ai_response),
				"confidence": 1.0
			}],
			relationships=[]
		)

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

	# Check if user is asking about the AI assistant
	ai_question_keywords = [
		'تو کی هستی', 'تو کجا توسعه پیدا کردی', 'چه کسی نوشته ات', 'چه کسی توسعه داده ات',
		'کجا آموزش دیده ای', 'توسعه دهنده تو کیست', 'نویسنده تو کیست', 'چه کسی تو را ساخته',
		'who are you', 'who created you', 'who developed you', 'who wrote you',
		'where were you developed', 'where were you trained'
	]
	is_ai_question = any(keyword in req.text.lower() for keyword in ai_question_keywords)
	
	if is_ai_question:
		ai_response = """من دستیار هوش مصنوعی هستم که در مرکز مدیریت و تحلیل داده فراجا و اداره مهندسی داده توسعه داده شده و آموزش دیده‌ام. توسعه‌دهنده من، سرهنگ مهندس علی سلیمی است و آماده‌ام تا شما را راهنمایی کنم."""
		return MultiModelResponse(
			text=req.text,
			language=language,
			domain=domain,
			first_analysis=ModelAnalysis(
				entities=[{
					"text": ai_response,
					"label": "AI_Response",
					"start": 0,
					"end": len(ai_response),
					"confidence": 1.0
				}],
				relationships=[]
			),
			second_analysis=ModelAnalysis(
				entities=[{
					"text": ai_response,
					"label": "AI_Response",
					"start": 0,
					"end": len(ai_response),
					"confidence": 1.0
				}],
				relationships=[]
			),
			final_analysis=ModelAnalysis(
				entities=[{
					"text": ai_response,
					"label": "AI_Response",
					"start": 0,
					"end": len(ai_response),
					"confidence": 1.0
				}],
				relationships=[]
			),
			agreement_score=1.0,
			conflicting_entities=[],
			conflicting_relationships=[]
		)

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


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
	"""Chat endpoint for conversational analysis with single/multi model support"""
	if not req.message or not req.message.strip():
		raise HTTPException(status_code=400, detail="'message' is required")

	language = (req.language or "fa").lower()
	domain = req.domain or "general"
	analysis_mode = req.analysisMode or "single"
	model_name = req.model or config.OLLAMA_MODEL

	try:
		# Build a conversational prompt based on domain
		domain_titles = {
			"police": "دستیار هوشمند امنیتی و پلیسی",
			"legal": "دستیار هوشمند حقوقی", 
			"medical": "دستیار هوشمند پزشکی",
			"general": "دستیار هوشمند عمومی"
		}
		
		domain_expertise = {
			"police": "شما متخصص تحلیل متون امنیتی، پلیسی، جرایم، تهدیدات و موارد مشکوک هستید.",
			"legal": "شما متخصص تحلیل متون حقوقی، قوانین، قراردادها، دادگاه‌ها و مسائل قانونی هستید.",
			"medical": "شما متخصص تحلیل متون پزشکی، تشخیص‌ها، درمان‌ها، داروها و مسائل سلامت هستید.",
			"general": "شما متخصص تحلیل متون عمومی و استخراج اطلاعات ساختاریافته هستید."
		}
		
		title = domain_titles.get(domain, domain_titles["general"])
		expertise = domain_expertise.get(domain, domain_expertise["general"])
		
		analysis_mode_desc = "با داوری چندمدله" if analysis_mode == "multi" else ""
		
		# Enhanced system prompt that considers conversation history
		history_context = ""
		if req.message_history and len(req.message_history) > 0:
			# Analyze conversation history to provide better context
			user_messages = [msg.content for msg in req.message_history if msg.role == "user"]
			assistant_messages = [msg.content for msg in req.message_history if msg.role == "assistant"]
			
			# Extract key topics and names mentioned
			all_content = " ".join([msg.content for msg in req.message_history])
			key_topics = []
			
			# Look for names, places, and important topics
			import re
			name_patterns = [r'نام\s+من\s+(\w+)', r'اسم\s+من\s+(\w+)', r'من\s+(\w+)\s+هستم', r'(\w+)\s+هستم']
			for pattern in name_patterns:
				matches = re.findall(pattern, all_content, re.IGNORECASE)
				key_topics.extend(matches)
			
			# Look for important topics
			topic_keywords = ['مشکل', 'خطا', 'اشتباه', 'کمک', 'راهنمایی', 'تحلیل', 'بررسی', 'سوال', 'پاسخ', 'توضیح']
			for keyword in topic_keywords:
				if keyword in all_content.lower():
					key_topics.append(keyword)
			
			# Look for questions
			question_patterns = [r'(\w+)\s+چیه', r'(\w+)\s+کیست', r'(\w+)\s+کجاست', r'چطور\s+(\w+)']
			for pattern in question_patterns:
				matches = re.findall(pattern, all_content, re.IGNORECASE)
				key_topics.extend(matches)
			
			topics_context = ""
			if key_topics:
				topics_context = f"\nموضوعات مهم در مکالمه: {', '.join(set(key_topics))}"
			
			# Analyze conversation length and complexity
			total_chars = sum(len(msg.content) for msg in req.message_history)
			avg_length = total_chars / len(req.message_history) if req.message_history else 0
			
			complexity_context = ""
			if len(req.message_history) > 10:
				complexity_context = "\nاین یک مکالمه طولانی است. لطفاً سابقه کامل را در نظر بگیرید."
			elif avg_length > 100:
				complexity_context = "\nمکالمه شامل پیام‌های طولانی است. لطفاً جزئیات را در نظر بگیرید."
			
			history_context = f"""
مهم: شما در حال ادامه یک مکالمه هستید. لطفاً سابقه مکالمه قبلی را در نظر بگیرید و پاسخ‌های خود را بر اساس آن ارائه دهید.

دستورالعمل‌های مهم:
- همیشه سابقه مکالمه را بررسی کنید
- اگر کاربر به موضوعات قبلی اشاره می‌کند، از سابقه استفاده کنید
- پاسخ‌های خود را بر اساس زمینه مکالمه ارائه دهید
- اگر کاربر سوال جدیدی می‌پرسد، آن را در ارتباط با سابقه پاسخ دهید

{topics_context}{complexity_context}

تعداد پیام‌های قبلی: {len(req.message_history)}
توجه: این مکالمه ادامه دارد، پس حتماً سابقه را در نظر بگیرید."""
		
		system_prompt = f"""شما {title} {analysis_mode_desc} مرکز مدیریت و تحلیل داده فراجا هستید.
{expertise}

قوانین مهم برای پاسخ‌دهی:
1. همیشه سابقه مکالمه را در نظر بگیرید
2. اگر کاربر به موضوعات قبلی اشاره می‌کند، از سابقه استفاده کنید
3. پاسخ‌های خود را کوتاه، مفید و به زبان {language} ارائه دهید
4. در صورت نیاز تحلیل متن یا نمودار ارائه دهید

قابلیت‌های ویژه شما:
- تحلیل متون و استخراج موجودیت‌ها و روابط
- کشیدن نمودار برای نمایش داده‌ها
- پاسخ‌دهی بر اساس سابقه مکالمه
- ارجاع به پیام‌های قبلی

برای کشیدن نمودار، از فرمت زیر استفاده کنید:
```chart
{{
  "type": "bar|line|pie|doughnut",
  "title": "عنوان نمودار",
  "labels": ["برچسب1", "برچسب2", "برچسب3"],
  "datasets": [
    {{
      "label": "نام مجموعه داده",
      "data": [10, 20, 30],
      "backgroundColor": ["#3b82f6", "#10b981", "#f59e0b"]
    }}
  ]
}}
```

{history_context}"""

		# Check if user is asking about the AI assistant
		ai_question_keywords = [
			'تو کی هستی', 'تو کجا توسعه پیدا کردی', 'چه کسی نوشته ات', 'چه کسی توسعه داده ات',
			'کجا آموزش دیده ای', 'توسعه دهنده تو کیست', 'نویسنده تو کیست', 'چه کسی تو را ساخته',
			'who are you', 'who created you', 'who developed you', 'who wrote you',
			'where were you developed', 'where were you trained'
		]
		is_ai_question = any(keyword in req.message.lower() for keyword in ai_question_keywords)
		
		if is_ai_question:
			ai_response = """من دستیار هوش مصنوعی هستم که در مرکز مدیریت و تحلیل داده فراجا و اداره مهندسی داده توسعه داده شده و آموزش دیده‌ام. توسعه‌دهنده من، سرهنگ مهندس علی سلیمی است و آماده‌ام تا شما را راهنمایی کنم."""
			return ChatResponse(message=ai_response)
		
		# Check if user wants analysis
		analysis_keywords = ['تحلیل', 'استخراج', 'موجودیت', 'رابطه', 'analyze', 'extract', 'بررسی', 'شناسایی']
		wants_analysis = any(keyword in req.message.lower() for keyword in analysis_keywords)

		if wants_analysis and len(req.message) > 50:
			# Perform analysis based on mode
			try:
				if analysis_mode == "multi" and req.model_first and req.model_second and req.model_referee:
					# Multi-model analysis
					analysis_result = run_multi_model_analysis(
						text=req.message,
						language=language,
						domain=domain,
						model_first=req.model_first,
						model_second=req.model_second,
						model_referee=req.model_referee,
						temperature=0.1,
						max_output_tokens=512,
						request_timeout_seconds=config.REQUEST_TIMEOUT_SECONDS,
						num_ctx=config.NUM_CTX,
					)
					
					entities_count = len(analysis_result["final_analysis"]["entities"])
					relationships_count = len(analysis_result["final_analysis"]["relationships"])
					agreement = analysis_result.get("agreement_score", 0) * 100
					conflicts = len(analysis_result.get("conflicting_entities", [])) + len(analysis_result.get("conflicting_relationships", []))
					
					response_message = f"""متن شما با داوری چندمدله تحلیل شد:
⚖️ نتیجه نهایی داور:
- {entities_count} موجودیت شناسایی شد
- {relationships_count} رابطه یافت شد
- میزان توافق مدل‌ها: {agreement:.1f}%
- تعارضات شناسایی شده: {conflicts}

جزئیات کامل در پنل زیر نمایش داده شده است."""

					# Convert to format expected by frontend
					formatted_result = {
						"text": analysis_result["text"],
						"language": analysis_result["language"],
						"domain": analysis_result["domain"],
						"first_analysis": analysis_result["first_analysis"],
						"second_analysis": analysis_result["second_analysis"],
						"final_analysis": analysis_result["final_analysis"],
						"agreement_score": analysis_result["agreement_score"],
						"conflicting_entities": analysis_result["conflicting_entities"],
						"conflicting_relationships": analysis_result["conflicting_relationships"],
					}

					return ChatResponse(
						message=response_message,
						analysis=formatted_result,
						analysisMode="multi"
					)
				else:
					# Single model analysis
					analysis_result = run_extraction(
						text=req.message,
						language=language,
						domain=domain,
						model=model_name,
						temperature=0.1,
						max_output_tokens=512
					)
					
					entities_count = len(analysis_result.get("entities", []))
					relationships_count = len(analysis_result.get("relationships", []))
					
					response_message = f"""متن شما تحلیل شد:
- {entities_count} موجودیت شناسایی شد
- {relationships_count} رابطه یافت شد

جزئیات در پنل زیر نمایش داده شده است."""

					# Convert to format expected by frontend
					formatted_result = {
						"text": req.message,
						"language": language,
						"model": model_name,
						"entities": analysis_result.get("entities", []),
						"relationships": analysis_result.get("relationships", []),
					}

					return ChatResponse(
						message=response_message,
						analysis=formatted_result,
						analysisMode="single"
					)
			except Exception as e:
				print(f"Analysis failed: {str(e)}")
				pass  # Fall back to regular chat

		# Regular chat response with message history support
		
		# Convert message history to the format expected by ollama
		message_history = []
		if req.message_history:
			for msg in req.message_history:
				message_history.append({
					"role": msg.role,
					"content": msg.content
				})
			print(f"📝 Received message history: {len(message_history)} messages")
			for i, msg in enumerate(message_history):
				print(f"  {i+1}. {msg['role']}: {msg['content'][:50]}...")
			
			# Validate message history format
			if len(message_history) > 0:
				print(f"📝 First message: {message_history[0]['role']}: {message_history[0]['content'][:30]}...")
				print(f"📝 Last message: {message_history[-1]['role']}: {message_history[-1]['content'][:30]}...")
				
				# Analyze message patterns
				user_messages = [msg for msg in message_history if msg['role'] == 'user']
				assistant_messages = [msg for msg in message_history if msg['role'] == 'assistant']
				print(f"📝 Message analysis: {len(user_messages)} user, {len(assistant_messages)} assistant")
				
				# Check for important patterns
				all_content = " ".join([msg['content'] for msg in message_history])
				if 'نام' in all_content or 'اسم' in all_content:
					print("📝 Contains name/identity information")
				if 'مشکل' in all_content or 'خطا' in all_content:
					print("📝 Contains problem/error information")
				if '؟' in all_content or '?' in all_content:
					print("📝 Contains questions")
		
		# Adjust parameters based on conversation complexity
		temperature = 0.7
		max_tokens = 256
		
		if req.message_history and len(req.message_history) > 10:
			# For long conversations, use lower temperature for consistency
			temperature = 0.5
			max_tokens = 512  # Allow longer responses for complex conversations
			print("📝 Adjusting parameters for long conversation")
		
		response = chat_conversational(
			system_prompt=system_prompt,
			user_message=req.message,
			model=model_name,
			message_history=message_history if message_history else None,
			temperature=temperature,
			max_output_tokens=max_tokens
		)

		# Clean up response
		clean_response = response.strip()
		if clean_response.startswith('"') and clean_response.endswith('"'):
			clean_response = clean_response[1:-1]
		
		# Extract chart data if present
		chart_data = None
		import re
		chart_pattern = r'```chart\s*\n(.*?)\n```'
		chart_match = re.search(chart_pattern, clean_response, re.DOTALL)
		if chart_match:
			try:
				import json
				chart_json = chart_match.group(1).strip()
				chart_data = json.loads(chart_json)
				# Remove chart block from response text
				clean_response = re.sub(chart_pattern, '', clean_response, flags=re.DOTALL).strip()
				print(f"📊 Chart data extracted: {chart_data.get('type', 'unknown')} chart")
			except json.JSONDecodeError as e:
				print(f"⚠️ Failed to parse chart JSON: {e}")
				chart_data = None

		# Log response quality
		print(f"📝 Response length: {len(clean_response)} characters")
		if len(clean_response) < 10:
			print("⚠️ Warning: Very short response")
		elif len(clean_response) > 500:
			print("📝 Long response generated")
		
		# Check if response seems to consider history
		if req.message_history and len(req.message_history) > 0:
			history_indicators = ['قبلاً', 'سابقاً', 'گفتم', 'گفتید', 'قبل', 'پیش', 'همان', 'همین']
			considers_history = any(indicator in clean_response for indicator in history_indicators)
			if considers_history:
				print("✅ Response appears to consider conversation history")
			else:
				print("⚠️ Response may not be considering conversation history")
			
			# Check for specific references to previous messages
			has_specific_reference = any(
				msg.content in clean_response or 
				(len(msg.content) > 10 and msg.content[:10] in clean_response)
				for msg in req.message_history
			)
			if has_specific_reference:
				print("✅ Response contains specific reference to previous message")
			
			# Check for continuity in conversation
			has_continuity = any(
				msg.role == 'user' and msg.content.lower()[:5] in clean_response.lower()
				for msg in req.message_history
			)
			if has_continuity:
				print("✅ Response shows good conversation continuity")
			
			# Check for context awareness
			has_context_awareness = any(
				msg.role == 'assistant' and msg.content.lower()[:5] in clean_response.lower()
				for msg in req.message_history
			)
			if has_context_awareness:
				print("✅ Response shows context awareness from previous assistant messages")
			
			# Overall conversation quality assessment
			quality_indicators = [
				considers_history,
				has_specific_reference,
				has_continuity,
				has_context_awareness
			]
			quality_score = sum(quality_indicators)
			print(f"📝 Conversation quality score: {quality_score}/4")
			
			if quality_score >= 3:
				print("✅ Excellent conversation quality")
			elif quality_score >= 2:
				print("✅ Good conversation quality")
			elif quality_score >= 1:
				print("⚠️ Fair conversation quality")
			else:
				print("⚠️ Poor conversation quality - may not be considering history")
			
			# Store quality score for potential future use
			if quality_score < 2:
				print("⚠️ Consider improving conversation context or model parameters")
			
			# Log conversation summary for debugging
			print(f"📝 Conversation summary: {len(req.message_history)} messages, quality: {quality_score}/4")
			if req.message_history:
				last_user_message = next((msg for msg in reversed(req.message_history) if msg.role == 'user'), None)
				last_assistant_message = next((msg for msg in reversed(req.message_history) if msg.role == 'assistant'), None)
				if last_user_message:
					print(f"📝 Last user message: \"{last_user_message.content[:50]}...\"")
				if last_assistant_message:
					print(f"📝 Last assistant message: \"{last_assistant_message.content[:50]}...\"")
			
			# Log current message for context
			print(f"📝 Current user message: \"{req.message[:50]}...\"")
			print(f"📝 Current assistant response: \"{clean_response[:50]}...\"")
			
			# Log conversation flow for debugging
			print(f"📝 Conversation flow: {len(req.message_history)} previous messages → current exchange")
			if req.message_history:
				user_messages = sum(1 for msg in req.message_history if msg.role == 'user')
				assistant_messages = sum(1 for msg in req.message_history if msg.role == 'assistant')
				print(f"📝 Previous flow: {user_messages} user messages, {assistant_messages} assistant messages")
			
			# Log conversation quality metrics
			print(f"📝 Quality metrics: History consideration: {considers_history}, Specific refs: {has_specific_reference}, Continuity: {has_continuity}, Context awareness: {has_context_awareness}")
			
			# Log conversation health check
			health_check = {
				'has_history': len(req.message_history) > 0,
				'has_quality': quality_score >= 2,
				'has_continuity': has_continuity,
				'has_context': has_context_awareness
			}
			print(f"📝 Conversation health check: {health_check}")
			
			if not health_check['has_history']:
				print("⚠️ No conversation history available")
			if not health_check['has_quality']:
				print("⚠️ Low conversation quality detected")
			
			# Log conversation improvement suggestions
			if quality_score < 2:
				print("💡 Suggestions for better conversation quality:")
				if not considers_history:
					print("  - Model may need better history context")
				if not has_specific_reference:
					print("  - Model may need to reference specific previous messages")
				if not has_continuity:
					print("  - Model may need better conversation continuity")
				if not has_context_awareness:
					print("  - Model may need better context awareness")

		return ChatResponse(message=clean_response, chart=chart_data)

	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@app.post("/api/chat-speech-to-text", response_model=SpeechToTextResponse)
async def chat_speech_to_text(
	audio_file: UploadFile = File(...),
	language: str = Form("fa"),
	use_hybrid: bool = Form(True),
	model_preference: str = Form("auto")
) -> SpeechToTextResponse:
	"""Convert speech to text for chatbot using hybrid Persian models"""
	try:
		# Prepare form data for the speech-to-text service
		files = {"audio_file": (audio_file.filename, await audio_file.read(), audio_file.content_type)}
		
		# Choose endpoint based on hybrid preference
		if use_hybrid:
			endpoint = "http://localhost:8001/transcribe-hybrid"
			data = {
				"language": language, 
				"model_preference": model_preference
			}
		else:
			endpoint = "http://localhost:8001/transcribe-chat"
			data = {
				"language": language
			}
		
		# Call the speech-to-text microservice
		async with httpx.AsyncClient(timeout=120.0) as client:  # Increased timeout for hybrid processing
			response = await client.post(
				endpoint,
				files=files,
				data=data
			)
			
			if response.status_code != 200:
				raise HTTPException(
					status_code=response.status_code,
					detail=f"Speech-to-text service error: {response.text}"
				)
			
			result = response.json()
			
			# Handle hybrid response format
			hybrid_results = result.get("hybrid_results")
			if hybrid_results:
				# Log hybrid analysis for debugging
				print(f"🎯 Chat hybrid transcription completed:")
				print(f"   Model used: {result.get('model_used', 'unknown')}")
				print(f"   Confidence: {result.get('confidence', 0.0)}")
				print(f"   Models compared: {hybrid_results.get('models_compared', 0)}")
				if hybrid_results.get('similarity'):
					print(f"   Similarity: {hybrid_results['similarity']:.2f}")
			
			return SpeechToTextResponse(
				text=result["text"],
				language=result["language"],
				confidence=result.get("confidence")
			)
			
	except httpx.RequestError as e:
		raise HTTPException(status_code=503, detail=f"Speech-to-text service unavailable: {str(e)}")
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Speech-to-text failed: {str(e)}")

@app.post("/api/speech-to-text", response_model=SpeechToTextResponse)
async def speech_to_text(
	audio_file: UploadFile = File(...),
	language: str = Form("fa"),
	use_hybrid: bool = Form(True),
	model_preference: str = Form("auto")
) -> SpeechToTextResponse:
	"""Convert speech to text using the hybrid Persian speech-to-text microservice"""
	try:
		# Prepare form data for the speech-to-text service
		files = {"audio_file": (audio_file.filename, await audio_file.read(), audio_file.content_type)}
		
		# Choose endpoint based on hybrid preference
		if use_hybrid:
			endpoint = "http://localhost:8001/transcribe-hybrid"
			data = {
				"language": language, 
				"model_preference": model_preference
			}
		else:
			endpoint = "http://localhost:8001/transcribe"
			data = {
				"language": language, 
				"model_size": "large"
			}
		
		# Call the speech-to-text microservice
		async with httpx.AsyncClient(timeout=120.0) as client:  # Increased timeout for hybrid processing
			response = await client.post(
				endpoint,
				files=files,
				data=data
			)
			
			if response.status_code != 200:
				raise HTTPException(
					status_code=response.status_code,
					detail=f"Speech-to-text service error: {response.text}"
				)
			
			result = response.json()
			
			# Handle hybrid response format
			hybrid_results = result.get("hybrid_results")
			if hybrid_results:
				# Log hybrid analysis for debugging
				print(f"🎯 Hybrid transcription completed:")
				print(f"   Model used: {result.get('model_used', 'unknown')}")
				print(f"   Confidence: {result.get('confidence', 0.0)}")
				print(f"   Models compared: {hybrid_results.get('models_compared', 0)}")
				if hybrid_results.get('similarity'):
					print(f"   Similarity: {hybrid_results['similarity']:.2f}")
			
			return SpeechToTextResponse(
				text=result["text"],
				language=result["language"],
				confidence=result.get("confidence")
			)
			
	except httpx.RequestError as e:
		raise HTTPException(status_code=503, detail=f"Speech-to-text service unavailable: {str(e)}")
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Speech-to-text failed: {str(e)}")
