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
from . import es as esmod
from .es_query_handler import ESQueryHandler

# Add shared package to sys.path
CURRENT_DIR = os.path.dirname(__file__)
MONOREPO_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
SHARED_DIR = os.path.join(MONOREPO_ROOT, "shared")
if SHARED_DIR not in sys.path:
	sys.path.insert(0, SHARED_DIR)

# System Identity Configuration
SYSTEM_NAME = "Mentora"
SYSTEM_NAME_ENGLISH = "Mentora"
DEVELOPER_NAME = "سرهنگ مهندس علی سلیمی"
DEVELOPER_NAME_ENGLISH = "Engineer Colonel Ali Salimi"
ORGANIZATION = "Mentora"

def get_system_identity_response() -> str:
	"""Get standardized system identity response"""
	return f"""سلام! من {SYSTEM_NAME} ({SYSTEM_NAME_ENGLISH}) هستم، دستیار هوشمند Mentora و متن شما.

🤖 درباره من:
- نام: {SYSTEM_NAME} ({SYSTEM_NAME_ENGLISH})
- توسعه‌دهنده: {DEVELOPER_NAME}
- سازمان: {ORGANIZATION}

🎯 قابلیت‌های من:
- تحلیل و استخراج اطلاعات از متن
- رسم نمودارهای تحلیلی و بصری‌سازی داده‌ها
- پاسخ‌دهی هوشمند با در نظر گیری سابقه مکالمه
- پشتیبانی از چندین مدل تحلیل همزمان

در خدمت شما هستم! چطور می‌تونم کمکتون کنم؟"""

# Import shared langextract after adjusting path
from langextract import run_extraction, run_multi_model_analysis, generate_html_report, list_schemas  # type: ignore
from langextract.ollama_backend import chat_conversational  # type: ignore

app = FastAPI(title="LangExtract Service", version="0.2.0")

# Initialize ES Query Handler
es_query_handler = ESQueryHandler()

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
	return DomainsResponse(domains=["general", "medical"])


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

@app.get("/api/config/tokens")
def get_token_config():
	"""Get current token configuration"""
	return {
		"max_output_tokens": config.MAX_OUTPUT_TOKENS,
		"num_ctx": config.NUM_CTX,
		"request_timeout": config.REQUEST_TIMEOUT_SECONDS,
		"max_input_chars": config.MAX_INPUT_CHARS
	}

@app.get("/api/chart/test")
def test_chart_parsing():
	"""Test endpoint for chart parsing functionality"""
	try:
		# Test cases for chart parsing
		test_cases = [
			{
				"name": "Complete chart",
				"input": '```chart\n{"type": "bar", "title": "تست", "labels": ["A", "B"], "datasets": [{"label": "داده", "data": [10, 20]}]}\n```',
				"expected": "success"
			},
			{
				"name": "Incomplete chart (missing closing)",
				"input": '```chart\n{"type": "bar", "title": "تست"',
				"expected": "fixed"
			},
			{
				"name": "No chart",
				"input": 'این متن نمودار ندارد',
				"expected": "none"
			}
		]
		
		results = []
		for test_case in test_cases:
			# Simulate chart parsing
			import re
			chart_pattern = r'```chart\s*\n(.*?)(?:\n```|$)'
			chart_match = re.search(chart_pattern, test_case["input"], re.DOTALL)
			
			if chart_match:
				chart_json = chart_match.group(1).strip()
				try:
					import json
					chart_data = json.loads(chart_json)
					result = "success"
				except json.JSONDecodeError:
					fixed_json = fix_incomplete_chart_json(chart_json)
					if fixed_json:
						try:
							chart_data = json.loads(fixed_json)
							result = "fixed"
						except:
							result = "failed"
					else:
						result = "failed"
			else:
				result = "none"
			
			results.append({
				"name": test_case["name"],
				"expected": test_case["expected"],
				"actual": result,
				"passed": result == test_case["expected"]
			})
		
		return {
			"status": "ok",
			"test_results": results,
			"all_passed": all(r["passed"] for r in results)
		}
		
	except Exception as e:
		return {"status": "error", "error": str(e)}


@app.get("/api/reports/overview")
def reports_overview(days: int = 7) -> Dict[str, Any]:
	"""Aggregate overview from Elasticsearch if enabled"""
	try:
		return esmod.reports_overview(days)
	except Exception as e:
		return {"enabled": False, "error": str(e)}


@app.get("/api/reports/search")
def reports_search(q: str, size: int = 20) -> Dict[str, Any]:
	"""Full-text search across user and assistant messages"""
	try:
		return esmod.search_messages(q, size=size)
	except Exception as e:
		return {"enabled": False, "error": str(e)}


@app.get("/api/reports/indices")
def reports_indices() -> Dict[str, Any]:
	"""List configured and existing indices in ES (if enabled)."""
	try:
		info = esmod.list_indices()
		# Friendly log to help user understand missing indices
		if info.get("enabled"):
			configured = info.get("configured", [])
			existing = info.get("existing", [])
			missing = info.get("missing", [])
			print(f"📚 ES indices → configured={configured} | existing={existing} | missing={missing}")
		return info
	except Exception as e:
		return {"enabled": False, "error": str(e)}


@app.get("/api/es/health")
def es_health() -> Dict[str, Any]:
	"""Detailed ES connection diagnostics (for logs/UI)."""
	try:
		info = esmod.health()
		print(f"🔎 ES health: {info}")
		return info
	except Exception as e:
		return {"enabled": False, "error": str(e)}


@app.get("/api/es/indices-fields")
def get_indices_with_fields() -> Dict[str, Any]:
	"""Get all Elasticsearch indices with their field mappings in tree structure."""
	try:
		info = esmod.get_all_indices_with_fields()
		return info
	except Exception as e:
		return {"enabled": False, "error": str(e)}


@app.get("/api/es/index-fields/{index_name}")
def get_index_fields(index_name: str) -> Dict[str, Any]:
	"""Get field mappings for a specific Elasticsearch index."""
	try:
		info = esmod.get_index_fields(index_name)
		return info
	except Exception as e:
		return {"enabled": False, "error": str(e)}

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

def fix_incomplete_chart_json(json_str: str) -> str:
	"""Try to fix incomplete or malformed chart JSON"""
	try:
		# Remove any trailing commas or incomplete parts
		json_str = json_str.strip()
		
		# If it ends with incomplete field, try to complete it
		if json_str.endswith('"title":'):
			json_str += ' "نمودار تحلیل"'
		elif json_str.endswith('"type":'):
			json_str += ' "bar"'
		elif json_str.endswith(','):
			json_str = json_str[:-1]  # Remove trailing comma
		
		# If JSON doesn't end with }, try to close it
		if not json_str.rstrip().endswith('}'):
			# Count open and close braces
			open_braces = json_str.count('{')
			close_braces = json_str.count('}')
			missing_braces = open_braces - close_braces
			
			# Add missing closing braces
			if missing_braces > 0:
				json_str += '}' * missing_braces
		
		# Try to parse and see if it's valid now
		import json
		parsed = json.loads(json_str)
		return json_str
		
	except Exception as e:
		print(f"🔧 JSON fix attempt failed: {e}")
		
		# Last resort: create a minimal valid chart
		try:
			# Extract type if available
			chart_type = "bar"  # default
			title = "نمودار تحلیل"  # default
			
			if '"type"' in json_str:
				import re
				type_match = re.search(r'"type":\s*"([^"]+)"', json_str)
				if type_match:
					chart_type = type_match.group(1)
			
			if '"title"' in json_str:
				title_match = re.search(r'"title":\s*"([^"]*)"', json_str)
				if title_match:
					title = title_match.group(1) or "نمودار تحلیل"
			
			# Create a minimal valid chart
			minimal_chart = {
				"type": chart_type,
				"title": title,
				"labels": ["داده ۱", "داده ۲", "داده ۳"],
				"datasets": [{
					"label": "مقادیر",
					"data": [10, 20, 15],
					"backgroundColor": ["rgba(59, 130, 246, 0.8)", "rgba(16, 185, 129, 0.8)", "rgba(245, 158, 11, 0.8)"]
				}]
			}
			
			print(f"🔧 Created minimal chart as fallback")
			return json.dumps(minimal_chart)
			
		except Exception as e2:
			print(f"❌ Failed to create minimal chart: {e2}")
			return None

def detect_chart_request(message: str) -> str:
	"""Detect if user is requesting a chart visualization.
	
	Returns the type of chart request detected, or None if no chart request found.
	"""
	message_lower = message.lower()
	
	# Direct chart request keywords
	direct_chart_keywords = [
		'نمودار', 'چارت', 'گراف', 'chart', 'graph', 'diagram',
		'رسم کن', 'بکش', 'نشان بده', 'نمایش بده', 'ترسیم کن',
		'تصویری نشان بده', 'بصری نشان بده', 'تصویر بکش',
		'شکل بکش', 'شکل نشان بده', 'تصویرسازی کن'
	]
	
	# Visualization request keywords (only explicit visualization terms)
	visualization_keywords = [
		'تجسم', 'بصری', 'visual', 'visualize', 'تصویرسازی',
		'نمایش داده', 'نمایش آمار', 'نمایش اعداد', 'visualization'
	]
	
	# Data presentation keywords (only specific data-related terms)
	data_keywords = [
		'داده', 'آمار', 'statistics', 'data', 'dataset',
		'عدد', 'رقم', 'مقدار عددی', 'اعداد'
	]
	
	# Chart type indicators
	chart_type_keywords = {
		'bar': ['میله', 'ستونی', 'بار', 'bar', 'column'],
		'line': ['خط', 'خطی', 'line', 'trend', 'روند'],
		'pie': ['دایره', 'پای', 'pie', 'circular', 'درصد'],
		'doughnut': ['حلقه', 'دونات', 'doughnut', 'ring']
	}
	
	# Strong indicators for chart requests - VERY EXPLICIT
	strong_indicators = [
		'نمودار بکش', 'چارت بکش', 'رسم کن', 'گراف بکش',
		'نمودار رسم کن', 'نمودار بده', 'نمودار نمایش بده',
		'chart draw', 'draw chart', 'visualize this', 'create chart',
		'یک نمودار', 'یه نمودار', 'نمودارش را', 'نمودارشو',
		'به شکل نمودار', 'در قالب نمودار', 'با نمودار نشان بده',
		'ترسیم کن', 'تصویر کن', 'بصری نشان بده', 'شکل بده',
		'نمودار میخوام', 'نمودار می‌خوام', 'chart میخوام'
	]
	
	# Check for strong indicators first
	for indicator in strong_indicators:
		if indicator in message_lower:
			print(f"📊 Strong chart indicator found: '{indicator}'")
			return "strong_request"
	
	# Check for direct chart keywords
	direct_count = sum(1 for keyword in direct_chart_keywords if keyword in message_lower)
	if direct_count > 0:
		print(f"📊 Direct chart keywords found: {direct_count}")
		return "direct_request"
	
	# Check for visualization + data combination
	viz_count = sum(1 for keyword in visualization_keywords if keyword in message_lower)
	data_count = sum(1 for keyword in data_keywords if keyword in message_lower)
	
	if viz_count > 0 and data_count > 0:
		print(f"📊 Visualization + data combination found: {viz_count} viz, {data_count} data")
		return "indirect_request"
	
	# Check for specific chart type requests
	for chart_type, keywords in chart_type_keywords.items():
		type_count = sum(1 for keyword in keywords if keyword in message_lower)
		if type_count > 0 and (viz_count > 0 or direct_count > 0):
			print(f"📊 Specific chart type requested: {chart_type}")
			return f"type_request_{chart_type}"
	
	# Check for comparative or analytical language that might benefit from charts
	# BUT ONLY if there are actual numbers or data to visualize
	analytical_patterns = [
		'مقایسه', 'تفاوت', 'بیشتر از', 'کمتر از', 'برتر از', 'بدتر از',
		'درصد', 'تعداد دقیق', 'میزان دقیق', 'سطح عددی', 'نرخ',
		'افزایش عددی', 'کاهش عددی', 'روند آماری', 'تغییر عددی'
	]
	
	# Check for actual numbers or quantitative data
	import re
	has_numbers = bool(re.search(r'\d+', message_lower))
	has_data_words = any(word in message_lower for word in ['آمار', 'داده', 'statistics', 'data'])
	
	analytical_count = sum(1 for pattern in analytical_patterns if pattern in message_lower)
	
	# Check for legal/security scenarios that should NOT have charts
	legal_indicators = [
		'شخصی', 'فردی', 'کسی', 'شخص', 'فرد',
		'مغازه', 'فروشگاه', 'دکان',
		'خریداری', 'فروش', 'خرید',
		'پرداخت', 'پول', 'فاکتور',
		'جرم', 'قانون', 'حقوقی', 'امنیتی', 'پلیسی'
	]
	
	legal_count = sum(1 for indicator in legal_indicators if indicator in message_lower)
	if legal_count >= 3:
		print(f"🚫 Legal/security scenario detected: {legal_count} indicators - NO CHART")
		return None
	
	# Only suggest chart for analytical content if there are actual numbers or data
	if analytical_count >= 2 and (has_numbers or has_data_words):
		print(f"📊 Analytical content with data detected: {analytical_count} indicators, numbers: {has_numbers}, data words: {has_data_words}")
		return "analytical_content"
	
	return None


def validate_and_complete_chart_data(chart_data: dict) -> dict:
	"""Validate and complete chart data structure"""
	try:
		# Required fields
		if not isinstance(chart_data, dict):
			return None
		
		# Ensure type is valid
		valid_types = ['bar', 'line', 'pie', 'doughnut']
		if 'type' not in chart_data or chart_data['type'] not in valid_types:
			chart_data['type'] = 'bar'  # default
		
		# Ensure title exists
		if 'title' not in chart_data or not chart_data['title']:
			chart_data['title'] = 'نمودار تحلیل'
		
		# Ensure labels exist
		if 'labels' not in chart_data or not isinstance(chart_data['labels'], list):
			chart_data['labels'] = ['داده ۱', 'داده ۲', 'داده ۳']
		
		# Ensure datasets exist and are valid
		if 'datasets' not in chart_data or not isinstance(chart_data['datasets'], list) or not chart_data['datasets']:
			chart_data['datasets'] = [{
				'label': 'مقادیر',
				'data': [10, 20, 15],
				'backgroundColor': ['rgba(59, 130, 246, 0.8)', 'rgba(16, 185, 129, 0.8)', 'rgba(245, 158, 11, 0.8)']
			}]
		
		# Validate each dataset
		for i, dataset in enumerate(chart_data['datasets']):
			if not isinstance(dataset, dict):
				chart_data['datasets'][i] = {
					'label': f'داده‌های {i+1}',
					'data': [10, 20, 15],
					'backgroundColor': ['rgba(59, 130, 246, 0.8)', 'rgba(16, 185, 129, 0.8)', 'rgba(245, 158, 11, 0.8)']
				}
				continue
			
			# Ensure label exists
			if 'label' not in dataset:
				dataset['label'] = f'داده‌های {i+1}'
			
			# Ensure data exists and is valid
			if 'data' not in dataset or not isinstance(dataset['data'], list):
				dataset['data'] = [10, 20, 15]
			
			# Ensure data length matches labels length
			if len(dataset['data']) != len(chart_data['labels']):
				# Adjust data to match labels
				labels_count = len(chart_data['labels'])
				if len(dataset['data']) > labels_count:
					dataset['data'] = dataset['data'][:labels_count]
				else:
					# Pad with zeros or repeat last value
					while len(dataset['data']) < labels_count:
						dataset['data'].append(dataset['data'][-1] if dataset['data'] else 10)
			
			# Add default colors if missing
			if 'backgroundColor' not in dataset:
				default_colors = [
					'rgba(59, 130, 246, 0.8)',
					'rgba(16, 185, 129, 0.8)', 
					'rgba(245, 158, 11, 0.8)',
					'rgba(239, 68, 68, 0.8)',
					'rgba(139, 92, 246, 0.8)',
					'rgba(236, 72, 153, 0.8)'
				]
				dataset['backgroundColor'] = default_colors[:len(chart_data['labels'])]
		
		return chart_data
		
	except Exception as e:
		print(f"❌ Chart validation failed: {e}")
		return None

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
		'کجا آموزش دیده ای', 'توسعه دهنده تو کیست', 'نویسنده تو کیست', 'چه کسی تو را ساخته','نویسنده تو چه کسی است',
		'نام تو چیست', 'اسم تو چیه', 'چی صدات کنم', 'Mentora', 'Mentora',
		'who are you', 'who created you', 'who developed you', 'who wrote you',
		'where were you developed', 'where were you trained', 'what is your name'
	]
	is_ai_question = any(keyword in req.text.lower() for keyword in ai_question_keywords)
	
	if is_ai_question:
		ai_response = get_system_identity_response()
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
		schema=req.schema_name or "general",
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
	schema_name: str = Form("general", alias="schema"),
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
		'نام تو چیست', 'اسم تو چیه', 'چی صدات کنم', 'Mentora', 'Mentora',
		'who are you', 'who created you', 'who developed you', 'who wrote you',
		'where were you developed', 'where were you trained', 'what is your name'
	]
	is_ai_question = any(keyword in text.lower() for keyword in ai_question_keywords)
	
	if is_ai_question:
		ai_response = get_system_identity_response()
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
		schema=schema_name or "general",
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
		schema=req.schema_name or "general",
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
		'نام تو چیست', 'اسم تو چیه', 'چی صدات کنم', 'Mentora', 'Mentora',
		'who are you', 'who created you', 'who developed you', 'who wrote you',
		'where were you developed', 'where were you trained', 'what is your name'
	]
	is_ai_question = any(keyword in req.text.lower() for keyword in ai_question_keywords)
	
	if is_ai_question:
		ai_response = get_system_identity_response()
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

	# Detect Elasticsearch intent: list indices
	def _detect_es_intent(message: str) -> Optional[str]:
		m = (message or "").lower()
		keywords_es = [
			"elasticsearch", "elastic", "الاستیک", "الیستیک", "الاستیک سرچ", "الاسلیک",
		]
		keywords_list = ["indices", "index", "ایندکس", "ایندکس ها", "ایندکس‌ها", "فهرست"]
		keywords_access = ["دسترسی", "کدام", "چه", "لیست", "نمایش"]
		if any(k in m for k in keywords_es) and any(k in m for k in keywords_list + keywords_access):
			return "list_indices"
		return None

	intent = _detect_es_intent(req.message)
	if intent == "list_indices":
		try:
			info = esmod.list_indices()
		except Exception as e:
			info = {"enabled": False, "error": str(e)}
		if not info.get("enabled"):
			return ChatResponse(message="ElasticSearch غیرفعال است (ES_ENABLED=false). برای فعال‌سازی، تنظیمات .env را بروزرسانی کنید.")
		if info.get("error"):
			return ChatResponse(message=f"خطا در بازیابی ایندکس‌ها: {info['error']}")
		
		# Show all available indices (dynamic discovery)
		all_indices = info.get("all_indices", [])
		total_indices = info.get("total_indices", 0)
		configured = info.get("configured", [])
		
		if not all_indices:
			return ChatResponse(message="📚 هیچ ایندکسی در کلاستر ElasticSearch یافت نشد.")
		
		text_lines = [
			f"📚 فهرست کامل ایندکس‌های ElasticSearch ({total_indices} ایندکس):",
			""
		]
		
		# Group indices: configured vs discovered
		configured_indices = [idx for idx in all_indices if idx.get("configured")]
		discovered_indices = [idx for idx in all_indices if not idx.get("configured")]
		
		if configured_indices:
			text_lines.append("🔧 ایندکس‌های پیکربندی شده:")
			for idx in configured_indices:
				name = idx.get("name", "")
				doc_count = idx.get("doc_count", "0")
				size = idx.get("size", "0b")
				try:
					doc_num = int(doc_count) if doc_count != "-" else 0
					doc_formatted = f"{doc_num:,}" if doc_num > 0 else "خالی"
				except:
					doc_formatted = doc_count
				text_lines.append(f"  • {name}: {doc_formatted} سند ({size})")
			text_lines.append("")
		
		if discovered_indices:
			text_lines.append("🔍 ایندکس‌های کشف شده (غیر پیکربندی):")
			for idx in discovered_indices:
				name = idx.get("name", "")
				doc_count = idx.get("doc_count", "0")
				size = idx.get("size", "0b")
				try:
					doc_num = int(doc_count) if doc_count != "-" else 0
					doc_formatted = f"{doc_num:,}" if doc_num > 0 else "خالی"
				except:
					doc_formatted = doc_count
				text_lines.append(f"  • {name}: {doc_formatted} سند ({size})")
		
		text_lines.append("")
		text_lines.append("💡 می‌توانید از هر کدام از این ایندکس‌ها برای جستجو استفاده کنید.")
		
		return ChatResponse(message="\n".join(text_lines))

	# SIMPLE DIRECT CHECK - if message contains mathematical operations OR simple listing and "price_usd", handle it directly
	needs_statistics = any(word in req.message.lower() for word in ['جمع', 'میانگین', 'مجموع', 'average', 'sum'])
	needs_simple_list = any(word in req.message.lower() for word in ['بده', 'give', 'show', 'لیست', 'list']) and not needs_statistics
	has_price_usd = 'price_usd' in req.message.lower()
	
	if (needs_statistics and has_price_usd) or (needs_simple_list and has_price_usd):
		try:
			# Direct implementation for list and sum
			es = esmod.get_client()
			if es:
				# Check if it's "last N records" query
				import re
				print(f"🎯 Testing message: '{req.message.lower()}'")
				# Try multiple patterns for different query types
				last_records_match = re.search(r'(\d+)\s*رکورد\s*اخر', req.message.lower())
				if not last_records_match:
					last_records_match = re.search(r'(\d+)\s*رکورد\s*آخر', req.message.lower())
				if not last_records_match:
					last_records_match = re.search(r'(\d+)\s*رکورد\s*آخرین', req.message.lower())
				if not last_records_match:
					# Pattern for "N رکورد اول"
					last_records_match = re.search(r'(\d+)\s*رکورد\s*اول', req.message.lower())
				if not last_records_match:
					# Pattern for "N رکورد اولین"
					last_records_match = re.search(r'(\d+)\s*رکورد\s*اولین', req.message.lower())
				if not last_records_match:
					# Pattern for "فقط N رکورد"
					last_records_match = re.search(r'فقط\s*(\d+)\s*رکورد', req.message.lower())
				if not last_records_match:
					# Pattern for "N رکورد را بده"
					last_records_match = re.search(r'(\d+)\s*رکورد\s*را\s*بده', req.message.lower())
				print(f"🎯 Pattern match result: {last_records_match}")
				size = 10000  # default
				sort_field = None
				sort_order = "desc"
				
				if last_records_match:
					size = int(last_records_match.group(1))
					# Check if it's a "last", "first", or just "N records" query
					if any(word in req.message.lower() for word in ['اخر', 'آخر', 'آخرین', 'last']):
						sort_field = "@timestamp"
						sort_order = "desc"
						print(f"🎯 Detected last {size} records query")
					elif any(word in req.message.lower() for word in ['اول', 'اولین', 'first']):
						sort_field = "@timestamp"
						sort_order = "asc"
						print(f"🎯 Detected first {size} records query")
					else:
						sort_field = None
						print(f"🎯 Detected {size} records query (no specific order)")
					print(f"🎯 Size will be set to: {size}")
				
				# Check if Date field is explicitly requested
				needs_date = any(word in req.message.lower() for word in ['date', 'تاریخ', 'تاریخ'])
				
				# Simple query with proper sorting for last N records
				# Build _source fields based on what's needed
				source_fields = ["Price_USD", "_id"]
				if needs_date:
					source_fields.append("Date")
				
				search_body = {
					"query": {"exists": {"field": "Price_USD"}},
					"size": size,
					"_source": source_fields
				}
				
				# Add sorting if it's a "last" or "first" records query
				if last_records_match and sort_field:
					search_body["sort"] = [{"@timestamp": {"order": sort_order}}]
					print(f"🎯 Added sort: {search_body['sort']}")
				elif last_records_match:
					print(f"🎯 No sorting added (just {size} records)")
				
				print(f"🎯 Final search_body: {search_body}")
				
				response = es.search(
					index="gold_data-2025.09.29",
					body=search_body,
					ignore_unavailable=True,
					allow_no_indices=True
				)
				
				# Process hits response
				hits = response.get('hits', {}).get('hits', [])
				print(f"🎯 Got {len(hits)} hits from ES")
				id_value_pairs = []
				cleaned_values = []
				
				for hit in hits:
					source = hit.get('_source', {})
					doc_id = hit.get('_id', '')
					if 'Price_USD' in source:
						raw_value = source['Price_USD']
						pair_data = {'id': doc_id, 'value': raw_value}
						
						# Only add date if it was requested
						if needs_date:
							date_value = source.get('Date', 'نامشخص')
							pair_data['date'] = date_value
						
						id_value_pairs.append(pair_data)
						
						# Clean numeric value
						try:
							cleaned = float(str(raw_value).replace('$', '').replace(',', '').replace('-', ''))
							cleaned_values.append(cleaned)
						except:
							pass
				
				# Detect all statistical operations needed (only if statistics are requested)
				needs_sum = any(word in req.message.lower() for word in ['جمع', 'مجموع', 'sum'])
				needs_average = any(word in req.message.lower() for word in ['میانگین', 'average', 'avg'])
				needs_min = any(word in req.message.lower() for word in ['حداقل', 'کمترین', 'کوچکترین', 'min', 'minimum'])
				needs_max = any(word in req.message.lower() for word in ['حداکثر', 'بیشترین', 'بزرگترین', 'مشخص کن', 'max', 'maximum'])
				needs_count = any(word in req.message.lower() for word in ['فراوانی', 'تعداد', 'count', 'frequency'])
				needs_std = any(word in req.message.lower() for word in ['انحراف', 'گریز', 'standard', 'std'])
				needs_median = any(word in req.message.lower() for word in ['میانه', 'median', 'مدین'])
				needs_mode = any(word in req.message.lower() for word in ['نما', 'mode', 'مد'])
				needs_variance = any(word in req.message.lower() for word in ['واریانس', 'variance', 'پراکندگی'])
				needs_range = any(word in req.message.lower() for word in ['دامنه', 'range', 'فاصله'])
				needs_growth = any(word in req.message.lower() for word in ['رشد', 'growth', 'نرخ رشد', 'افزایش'])
				needs_decline = any(word in req.message.lower() for word in ['کاهش', 'decline', 'نرخ کاهش', 'کم شدن'])
				needs_trend = any(word in req.message.lower() for word in ['روند', 'trend', 'گرایش'])
				
				# Check if any statistics are needed
				any_statistics_needed = any([needs_sum, needs_average, needs_min, needs_max, needs_count, needs_std, needs_median, needs_mode, needs_variance, needs_range, needs_growth, needs_decline, needs_trend])
				
				# Calculate all statistical measures
				if cleaned_values:
					sum_result = sum(cleaned_values)
					average_result = sum_result / len(cleaned_values)
					min_result = min(cleaned_values)
					max_result = max(cleaned_values)
					count_result = len(cleaned_values)
					
					# Standard deviation and variance
					variance = sum((x - average_result) ** 2 for x in cleaned_values) / len(cleaned_values)
					std_result = variance ** 0.5
					
					# Median calculation
					sorted_values = sorted(cleaned_values)
					n = len(sorted_values)
					if n % 2 == 0:
						median_result = (sorted_values[n//2 - 1] + sorted_values[n//2]) / 2
					else:
						median_result = sorted_values[n//2]
					
					# Mode calculation (most frequent value)
					from collections import Counter
					value_counts = Counter(cleaned_values)
					mode_result = value_counts.most_common(1)[0][0] if value_counts else 0
					
					# Range calculation
					range_result = max_result - min_result
					
					# Growth/Decline rate calculation (if we have time-ordered data)
					growth_rate = 0
					decline_rate = 0
					trend_result = "ثابت"
					
					if len(cleaned_values) >= 2:
						# Simple linear trend calculation
						first_half = cleaned_values[:len(cleaned_values)//2]
						second_half = cleaned_values[len(cleaned_values)//2:]
						
						first_avg = sum(first_half) / len(first_half)
						second_avg = sum(second_half) / len(second_half)
						
						if first_avg != 0:
							growth_rate = ((second_avg - first_avg) / first_avg) * 100
							decline_rate = -growth_rate if growth_rate < 0 else 0
							growth_rate = growth_rate if growth_rate > 0 else 0
							
							if growth_rate > 5:
								trend_result = "صعودی"
							elif decline_rate > 5:
								trend_result = "نزولی"
							else:
								trend_result = "ثابت"
				else:
					sum_result = average_result = min_result = max_result = count_result = std_result = 0
					median_result = mode_result = variance = range_result = 0
					growth_rate = decline_rate = 0
					trend_result = "نامشخص"
				
				print(f"🎯 Operations: sum={needs_sum}, avg={needs_average}, min={needs_min}, max={needs_max}, count={needs_count}, std={needs_std}")
				
				# Format response with HTML table - improved colors
				if last_records_match:
					if any(word in req.message.lower() for word in ['اخر', 'آخر', 'آخرین', 'last']):
						title = f"📋 لیست {size} رکورد آخر فیلد 'Price_USD' از ایندکس 'gold_data-2025.09.29'"
					elif any(word in req.message.lower() for word in ['اول', 'اولین', 'first']):
						title = f"📋 لیست {size} رکورد اول فیلد 'Price_USD' از ایندکس 'gold_data-2025.09.29'"
					else:
						title = f"📋 لیست {size} رکورد فیلد 'Price_USD' از ایندکس 'gold_data-2025.09.29'"
				else:
					title = f"📋 لیست {size} رکورد فیلد 'Price_USD' از ایندکس 'gold_data-2025.09.29'"
				# Build table header based on what fields are needed
				if needs_date:
					table_title = "📊 جدول ID، تاریخ و مقادیر:"
					table_headers = """<th style="border: 1px solid var(--border-color, #d1d5db); padding: 8px 6px; text-align: center; font-size: 0.9em; font-weight: 600; color: var(--text-color, #111827);">ردیف</th><th style="border: 1px solid var(--border-color, #d1d5db); padding: 8px 6px; text-align: center; font-size: 0.9em; font-weight: 600; color: var(--text-color, #111827);">ID</th><th style="border: 1px solid var(--border-color, #d1d5db); padding: 8px 6px; text-align: center; font-size: 0.9em; font-weight: 600; color: var(--text-color, #111827);">تاریخ</th><th style="border: 1px solid var(--border-color, #d1d5db); padding: 8px 6px; text-align: center; font-size: 0.9em; font-weight: 600; color: var(--text-color, #111827);">مقدار خام</th><th style="border: 1px solid var(--border-color, #d1d5db); padding: 8px 6px; text-align: center; font-size: 0.9em; font-weight: 600; color: var(--text-color, #111827);">مقدار پاک‌سازی شده</th>"""
					colspan_count = 5
				else:
					table_title = "📊 جدول ID و مقادیر:"
					table_headers = """<th style="border: 1px solid var(--border-color, #d1d5db); padding: 8px 6px; text-align: center; font-size: 0.9em; font-weight: 600; color: var(--text-color, #111827);">ردیف</th><th style="border: 1px solid var(--border-color, #d1d5db); padding: 8px 6px; text-align: center; font-size: 0.9em; font-weight: 600; color: var(--text-color, #111827);">ID</th><th style="border: 1px solid var(--border-color, #d1d5db); padding: 8px 6px; text-align: center; font-size: 0.9em; font-weight: 600; color: var(--text-color, #111827);">مقدار خام</th><th style="border: 1px solid var(--border-color, #d1d5db); padding: 8px 6px; text-align: center; font-size: 0.9em; font-weight: 600; color: var(--text-color, #111827);">مقدار پاک‌سازی شده</th>"""
					colspan_count = 4
				
				html_content = f"""<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 0;"><h3 style="margin: 0 0 8px 0; padding: 0; font-size: 1.1em; color: var(--text-color, #1a1a1a);">{title}</h3><h4 style="margin: 0 0 6px 0; padding: 0; font-size: 1em; color: var(--text-color, #2c2c2c);">{table_title}</h4><div style="overflow-x: auto; margin: 0;"><table style="border-collapse: collapse; width: 100%; margin: 0; border: 1px solid var(--border-color, #d1d5db); background: var(--bg-color, white);"><thead><tr style="background: var(--header-bg, #f3f4f6);">{table_headers}</tr></thead><tbody>"""
				
				# Show only the requested number of records
				display_count = size if last_records_match else min(len(id_value_pairs), 20)
				for i, pair in enumerate(id_value_pairs[:display_count], 1):
					doc_id = pair['id']  # نمایش کامل ID
					raw_value = str(pair['value'])[:20]
					
					try:
						cleaned = float(str(pair['value']).replace('$', '').replace(',', '').replace('-', ''))
						cleaned_str = f"{cleaned:,.2f}"
						row_bg = "var(--row-even-bg, #f8f9fa)" if i % 2 == 0 else "var(--row-odd-bg, transparent)"
					except:
						cleaned_str = "نامعتبر"
						row_bg = "var(--error-bg, #ffebee)"
					
					# Build row content based on whether date is needed
					if needs_date:
						date_value = pair.get('date', 'نامشخص')
						html_content += f"""<tr style="background: {row_bg};"><td style="border: 1px solid var(--border-color, #d1d5db); padding: 6px 4px; text-align: center; font-size: 0.85em; color: var(--text-color, #374151);">{i}</td><td style="border: 1px solid var(--border-color, #d1d5db); padding: 6px 4px; text-align: center; font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace; font-size: 0.8em; color: var(--text-color, #4b5563);">{doc_id}</td><td style="border: 1px solid var(--border-color, #d1d5db); padding: 6px 4px; text-align: center; font-size: 0.85em; color: var(--text-color, #374151);">{date_value}</td><td style="border: 1px solid var(--border-color, #d1d5db); padding: 6px 4px; text-align: center; font-size: 0.85em; color: var(--text-color, #374151);">{raw_value}</td><td style="border: 1px solid var(--border-color, #d1d5db); padding: 6px 4px; text-align: center; font-weight: 600; font-size: 0.85em; color: var(--success-color, #059669);">{cleaned_str}</td></tr>"""
					else:
						html_content += f"""<tr style="background: {row_bg};"><td style="border: 1px solid var(--border-color, #d1d5db); padding: 6px 4px; text-align: center; font-size: 0.85em; color: var(--text-color, #374151);">{i}</td><td style="border: 1px solid var(--border-color, #d1d5db); padding: 6px 4px; text-align: center; font-family: 'SF Mono', Monaco, 'Cascadia Code', monospace; font-size: 0.8em; color: var(--text-color, #4b5563);">{doc_id}</td><td style="border: 1px solid var(--border-color, #d1d5db); padding: 6px 4px; text-align: center; font-size: 0.85em; color: var(--text-color, #374151);">{raw_value}</td><td style="border: 1px solid var(--border-color, #d1d5db); padding: 6px 4px; text-align: center; font-weight: 600; font-size: 0.85em; color: var(--success-color, #059669);">{cleaned_str}</td></tr>"""
				
				if len(id_value_pairs) > display_count:
					html_content += f"""<tr style="background: var(--info-bg, #dbeafe);"><td colspan="{colspan_count}" style="border: 1px solid var(--border-color, #d1d5db); padding: 6px 4px; text-align: center; font-style: italic; font-size: 0.85em; color: var(--text-color, #4b5563);">... و {len(id_value_pairs) - display_count} مورد دیگر</td></tr>"""
				
				# Build summary section based on requested operations (only if statistics are needed)
				summary_html = ""
				if any_statistics_needed:
					summary_items = []
					summary_items.append(f'<div style="padding: 6px 8px; background: var(--item-bg, white); border-radius: 4px; border-left: 3px solid var(--border-color, #d1d5db);"><span style="font-weight: 600; color: var(--text-color, #374151);">تعداد کل مقادیر:</span> <span style="color: var(--text-color, #6b7280);">{len(id_value_pairs):,}</span></div>')
					summary_items.append(f'<div style="padding: 6px 8px; background: var(--item-bg, white); border-radius: 4px; border-left: 3px solid var(--border-color, #d1d5db);"><span style="font-weight: 600; color: var(--text-color, #374151);">تعداد مقادیر معتبر (عددی):</span> <span style="color: var(--text-color, #6b7280);">{len(cleaned_values):,}</span></div>')
				
				# Statistical measures with different colors
				if needs_sum:
					summary_items.append(f'<div style="padding: 8px 10px; background: var(--success-bg, #ecfdf5); border-radius: 4px; border-left: 4px solid var(--success-color, #10b981);"><span style="font-weight: 600; color: var(--text-color, #374151);">جمع مقادیر:</span> <span style="color: var(--success-color, #059669); font-size: 1.1em; font-weight: 700;">{sum_result:,.2f}</span></div>')
				
				if needs_average:
					summary_items.append(f'<div style="padding: 8px 10px; background: var(--info-bg, #dbeafe); border-radius: 4px; border-left: 4px solid var(--info-color, #3b82f6);"><span style="font-weight: 600; color: var(--text-color, #374151);">میانگین مقادیر:</span> <span style="color: var(--info-color, #1d4ed8); font-size: 1.1em; font-weight: 700;">{average_result:,.2f}</span></div>')
				
				if needs_min:
					summary_items.append(f'<div style="padding: 8px 10px; background: var(--warning-bg, #fef3c7); border-radius: 4px; border-left: 4px solid var(--warning-color, #f59e0b);"><span style="font-weight: 600; color: var(--text-color, #374151);">حداقل مقدار:</span> <span style="color: var(--warning-color, #d97706); font-size: 1.1em; font-weight: 700;">{min_result:,.2f}</span></div>')
				
				if needs_max:
					summary_items.append(f'<div style="padding: 8px 10px; background: var(--error-bg, #fee2e2); border-radius: 4px; border-left: 4px solid var(--error-color, #ef4444);"><span style="font-weight: 600; color: var(--text-color, #374151);">حداکثر مقدار:</span> <span style="color: var(--error-color, #dc2626); font-size: 1.1em; font-weight: 700;">{max_result:,.2f}</span></div>')
				
				if needs_count:
					summary_items.append(f'<div style="padding: 8px 10px; background: var(--purple-bg, #f3e8ff); border-radius: 4px; border-left: 4px solid var(--purple-color, #8b5cf6);"><span style="font-weight: 600; color: var(--text-color, #374151);">فراوانی (تعداد):</span> <span style="color: var(--purple-color, #7c3aed); font-size: 1.1em; font-weight: 700;">{count_result:,}</span></div>')
				
				if needs_std:
					summary_items.append(f'<div style="padding: 8px 10px; background: var(--teal-bg, #f0fdfa); border-radius: 4px; border-left: 4px solid var(--teal-color, #14b8a6);"><span style="font-weight: 600; color: var(--text-color, #374151);">انحراف معیار:</span> <span style="color: var(--teal-color, #0d9488); font-size: 1.1em; font-weight: 700;">{std_result:,.2f}</span></div>')
				
				if needs_median:
					summary_items.append(f'<div style="padding: 8px 10px; background: var(--indigo-bg, #e0e7ff); border-radius: 4px; border-left: 4px solid var(--indigo-color, #6366f1);"><span style="font-weight: 600; color: var(--text-color, #374151);">میانه:</span> <span style="color: var(--indigo-color, #4f46e5); font-size: 1.1em; font-weight: 700;">{median_result:,.2f}</span></div>')
				
				if needs_mode:
					summary_items.append(f'<div style="padding: 8px 10px; background: var(--pink-bg, #fce7f3); border-radius: 4px; border-left: 4px solid var(--pink-color, #ec4899);"><span style="font-weight: 600; color: var(--text-color, #374151);">نما (مد):</span> <span style="color: var(--pink-color, #db2777); font-size: 1.1em; font-weight: 700;">{mode_result:,.2f}</span></div>')
				
				if needs_variance:
					summary_items.append(f'<div style="padding: 8px 10px; background: var(--orange-bg, #fed7aa); border-radius: 4px; border-left: 4px solid var(--orange-color, #ea580c);"><span style="font-weight: 600; color: var(--text-color, #374151);">واریانس:</span> <span style="color: var(--orange-color, #c2410c); font-size: 1.1em; font-weight: 700;">{variance:,.2f}</span></div>')
				
				if needs_range:
					summary_items.append(f'<div style="padding: 8px 10px; background: var(--cyan-bg, #cffafe); border-radius: 4px; border-left: 4px solid var(--cyan-color, #06b6d4);"><span style="font-weight: 600; color: var(--text-color, #374151);">دامنه:</span> <span style="color: var(--cyan-color, #0891b2); font-size: 1.1em; font-weight: 700;">{range_result:,.2f}</span></div>')
				
				if needs_growth:
					summary_items.append(f'<div style="padding: 8px 10px; background: var(--emerald-bg, #d1fae5); border-radius: 4px; border-left: 4px solid var(--emerald-color, #10b981);"><span style="font-weight: 600; color: var(--text-color, #374151);">نرخ رشد:</span> <span style="color: var(--emerald-color, #059669); font-size: 1.1em; font-weight: 700;">{growth_rate:,.2f}%</span></div>')
				
				if needs_decline:
					summary_items.append(f'<div style="padding: 8px 10px; background: var(--rose-bg, #fecaca); border-radius: 4px; border-left: 4px solid var(--rose-color, #f43f5e);"><span style="font-weight: 600; color: var(--text-color, #374151);">نرخ کاهش:</span> <span style="color: var(--rose-color, #e11d48); font-size: 1.1em; font-weight: 700;">{decline_rate:,.2f}%</span></div>')
				
				if needs_trend:
					trend_color = "#10b981" if trend_result == "صعودی" else "#ef4444" if trend_result == "نزولی" else "#6b7280"
					summary_items.append(f'<div style="padding: 8px 10px; background: var(--gray-bg, #f3f4f6); border-radius: 4px; border-left: 4px solid {trend_color};"><span style="font-weight: 600; color: var(--text-color, #374151);">روند کلی:</span> <span style="color: {trend_color}; font-size: 1.1em; font-weight: 700;">{trend_result}</span></div>')
				
				summary_html = "".join(summary_items)
				
				# Add summary section only if statistics are needed
				if any_statistics_needed:
					html_content += f"""</tbody></table></div><div style="background: var(--summary-bg, #f9fafb); padding: 12px; border-radius: 6px; margin: 12px 0 0 0; border: 1px solid var(--border-color, #d1d5db);"><h4 style="margin: 0 0 8px 0; padding: 0; font-size: 0.95em; color: var(--text-color, #1f2937);">📊 خلاصه محاسبات:</h4><div style="display: flex; flex-direction: column; gap: 6px;">{summary_html}</div></div></div>"""
				else:
					html_content += f"""</tbody></table></div></div>"""
				
				return ChatResponse(message=html_content)
			else:
				return ChatResponse(message="❌ Elasticsearch غیرفعال است")
		except Exception as e:
			return ChatResponse(message=f"❌ خطا: {str(e)}")

	# Check if this is an ES query using the new advanced handler
	if es_query_handler.is_enabled():
		query_params = es_query_handler.parse_query(req.message)
		
		# If we detected a known query type, handle it with the advanced handler
		if query_params.query_type.value != "unknown":
			result = es_query_handler.execute_query(query_params)
			formatted_response = es_query_handler.format_response(result, query_params)
			
			# Include chart data if available
			chart_data = result.get("chart_data") if isinstance(result, dict) else None
			
			return ChatResponse(
				message=formatted_response,
				chart=chart_data
			)

		# Legacy ES handling - keeping as fallback
		# Detect ES count intent (e.g., تعداد رکوردهای ایندکس instagram ...)
		def _extract_index_for_count(message: str) -> Optional[str]:
			import re
			text_raw = (message or "").strip()
			text = text_raw.lower()
			# Must look like a counting question
			if not any(k in text for k in ["تعداد", "count", "چندتا", "چند تا"]):
				return None
			if not any(k in text for k in ["رکورد", "سند", "document", "doc", "documents"]):
				return None
			# 1) Persian pattern: "ایندکسی که با <name> شروع می شود/میشه"
			patterns = [
				r"ایندکس(?:ی)?\s*که\s*با\s*([A-Za-z0-9_.\-]+)\s*شروع\s*می\s*ش(?:ود|ه)",
				# 2) Persian order variant: "با <name> شروع می شود"
				r"با\s*([A-Za-z0-9_.\-]+)\s*شروع\s*می\s*ش(?:ود|ه)",
				# 3) English: "index that starts with <name>"
				r"index\s+(?:that\s+)?starts\s+with\s+([A-Za-z0-9_.\-]+)",
				# 4) After the word index/ایندکس try to capture next token
				r"(?:ایندکس|index|idx)\s*[:=,\-]?\s*([A-Za-z0-9_.\-]+)"
			]
			for pat in patterns:
				m = re.search(pat, text)
				if m:
					name = m.group(1)
					return f"{name}*"
			# 5) Fallback: pick the most likely latin token (e.g., instagram)
			candidates = re.findall(r"[A-Za-z][A-Za-z0-9_.\-]+", text)
			if candidates:
				# Prefer longer tokens
				candidates.sort(key=len, reverse=True)
				return f"{candidates[0]}*"
			return None

		idx_hint = _extract_index_for_count(req.message)
		if idx_hint:
			# Try direct count by pattern first (ES handles wildcard efficiently)
			direct = esmod.count_by_pattern(idx_hint)
			if not direct.get("enabled"):
				return ChatResponse(message="ElasticSearch غیرفعال است.")
			if direct.get("error") is None and isinstance(direct.get("count"), int):
				return ChatResponse(message=f"📊 مجموع رکوردها ({direct.get('pattern')}): {direct.get('count')}")
			# Fallback to enumerate matches and sum
			found = esmod.find_indices_like(idx_hint)
			if not found.get("enabled"):
				return ChatResponse(message="ElasticSearch غیرفعال است (ES_ENABLED=false). برای فعال‌سازی، تنظیمات .env را بروزرسانی کنید.")
			matches = found.get("matched", [])
			if not matches:
				return ChatResponse(message=f"ایندکسی با الگوی '{idx_hint}' یافت نشد.")
			cnt = esmod.count_documents(matches)
			if not cnt.get("enabled"):
				return ChatResponse(message="ElasticSearch غیرفعال است.")
			total = cnt.get("total", 0)
			return ChatResponse(message=f"📊 مجموع رکوردها ({', '.join(matches)}): {total}")

		# Detect ES fetch N documents intent
		def _extract_fetch_n(message: str) -> Optional[Dict[str, Any]]:
			import re
			text = (message or '').strip().lower()
			# Look for a number near رکورد/records
			num = None
			m = re.search(r"(\d{1,4})\s*(?:رکورد|records|docs?)", text)
			if m:
				num = int(m.group(1))
			# Extract index name similar to count
			name = _extract_index_for_count(message)
			if name or num:
				return {"name": name, "size": num or 10}
			return None

		fetch_req = _extract_fetch_n(req.message)
		if fetch_req and fetch_req.get("name"):
			res = esmod.fetch_documents_by_pattern(fetch_req["name"], size=int(fetch_req.get("size", 10)))
			if not res.get("enabled"):
				return ChatResponse(message="ElasticSearch غیرفعال است.")
			if res.get("error"):
				return ChatResponse(message=f"خطا در دریافت رکوردها: {res.get('error')}")
			docs = res.get("docs", [])
			if not docs:
				return ChatResponse(message=f"رکوردی با الگوی '{res.get('pattern')}' یافت نشد.")
			# Return compact preview of docs
			lines = [f"📄 {len(docs)} رکورد اول از '{res.get('pattern')}':"]
			for d in docs:
				idx = d.get("_index")
				_id = d.get("_id")
				src = d.get("_source")
				preview = src if isinstance(src, str) else (str(src)[:200] if src is not None else "{}")
				lines.append(f"- [{idx}] {_id}: {preview}")
			return ChatResponse(message="\n".join(lines))
		# Only check for charts if this is NOT an ES query
		chart_request_detected = None
		if es_query_handler.is_enabled():
			query_params = es_query_handler.parse_query(req.message)
			# Only check for charts if it's NOT an ES query (unknown, or not aggregate/list_and_sum)
			if query_params.query_type.value == "unknown" or query_params.query_type.value not in ["aggregate", "list_and_sum"]:
				chart_request_detected = detect_chart_request(req.message)
		else:
			chart_request_detected = detect_chart_request(req.message)
		
		if chart_request_detected:
			print(f"📊 Chart request detected: {chart_request_detected}")
		
	try:
		# Build a conversational prompt based on domain
		domain_titles = {
			"medical": "دستیار هوشمند پزشکی",
			"general": "دستیار هوشمند عمومی"
		}
		
		domain_expertise = {
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
			
			# Analyze message importance for enhanced context
			recent_messages_count = len([msg for msg in req.message_history[-5:] if msg.role == "user"])
			has_history_references = any(
				any(keyword in msg.content.lower() for keyword in ['قبلا', 'قبل', 'پیش', 'سابقه', 'گفت', 'یاد'])
				for msg in req.message_history[-3:] if msg.role == "user"
			)
			
			# Enhanced context instructions based on message patterns
			importance_instructions = ""
			if has_history_references:
				importance_instructions = """
⚠️ اولویت ویژه: کاربر به سابقه مکالمه اشاره کرده است. این بسیار مهم است!
- حتماً پیام‌های قبلی را با دقت بررسی کنید
- به موضوعات، نام‌ها، و جزئیات مطرح شده در سابقه توجه ویژه کنید
- پاسخ خود را مستقیماً به سابقه مرتبط کنید"""
			
			recency_instructions = f"""
📊 اولویت‌بندی پیام‌ها:
- پیام‌های جدیدتر اهمیت بالاتری دارند
- {recent_messages_count} پیام اخیر کاربر بیشترین اولویت را دارند
- پیام‌های حاوی سوال، نام، یا موضوعات مهم اولویت بالا دارند"""
			
			history_context = f"""
مهم: شما در حال ادامه یک مکالمه هستید. لطفاً سابقه مکالمه قبلی را در نظر بگیرید و پاسخ‌های خود را بر اساس آن ارائه دهید.

دستورالعمل‌های مهم:
- همیشه سابقه مکالمه را بررسی کنید
- اگر کاربر به موضوعات قبلی اشاره می‌کند، از سابقه استفاده کنید
- پاسخ‌های خود را بر اساس زمینه مکالمه ارائه دهید
- اگر کاربر سوال جدیدی می‌پرسد، آن را در ارتباط با سابقه پاسخ دهید
- پیام‌های جدیدتر اهمیت بیشتری دارند

{importance_instructions}

{recency_instructions}

{topics_context}{complexity_context}

تعداد پیام‌های قبلی: {len(req.message_history)}
توجه: این مکالمه ادامه دارد، پس حتماً سابقه را در نظر بگیرید."""
		
		# Enhanced chart instructions based on detection
		chart_instructions = ""
		if chart_request_detected:
			if chart_request_detected in ["strong_request", "direct_request"]:
				chart_instructions = """
🎯 **اولویت حتمی**: کاربر مستقیماً نمودار درخواست کرده است!
- **حتماً و قطعاً نمودار رسم کنید** - این دستور اجباری است
- حتی اگر داده کم یا ناقص است، باز هم نمودار بکشید
- اگر داده ندارید، از داده‌های نمونه یا فرضی استفاده کنید
- **هیچ بهانه‌ای برای نکشیدن نمودار قابل قبول نیست**
- نمودار باید مفصل، دقیق و زیبا باشد
- عنوان نمودار باید واضح و توصیفی باشد"""
			
			elif chart_request_detected == "indirect_request":
				chart_instructions = """
📊 توجه: کاربر به نمایش بصری داده‌ها علاقه دارد
- فقط اگر داده‌های عددی واقعی دارید، نمودار بکشید
- اگر سوال حقوقی، امنیتی یا توصیفی است، نمودار نکشید
- نمودار فقط برای داده‌های قابل اندازه‌گیری مناسب است"""
			
			elif chart_request_detected == "analytical_content":
				chart_instructions = """
📈 هوشیار باشید: محتوای تحلیلی با داده تشخیص داده شد
- فقط اگر اعداد یا آمار واقعی وجود دارد، نمودار بکشید
- برای سناریوهای حقوقی، امنیتی یا توصیفی نمودار نکشید
- نمودار فقط برای مقایسه داده‌های عددی استفاده کنید"""
		
		system_prompt = f"""شما {SYSTEM_NAME} ({SYSTEM_NAME_ENGLISH}) هستید، {title} {analysis_mode_desc} {ORGANIZATION}.
{expertise}

🤖 هویت شما:
- نام: {SYSTEM_NAME} ({SYSTEM_NAME_ENGLISH})
- توسعه‌دهنده: {DEVELOPER_NAME}
- اگر کسی از نام یا هویت شما پرسید، از این اطلاعات استفاده کنید
- هرگز نام تصادفی برای خود انتخاب نکنید - فقط از {SYSTEM_NAME} استفاده کنید

قوانین مهم برای پاسخ‌دهی:
1. همیشه سابقه مکالمه را در نظر بگیرید
2. اگر کاربر به موضوعات قبلی اشاره می‌کند، از سابقه استفاده کنید
3. پیام‌های جدیدتر اولویت بالاتری دارند - به آنها توجه بیشتری کنید
4. اگر کاربر به سابقه اشاره کرد (مثل "قبلا گفتم" یا "یادت هست") اهمیت ویژه دهید
5. پاسخ‌های خود را کوتاه، مفید و به زبان {language} ارائه دهید
6. فقط زمانی نمودار بکشید که داده‌های عددی واقعی وجود دارد یا کاربر صراحتاً درخواست کرده

{chart_instructions}

قابلیت‌های ویژه شما:
- تحلیل متون و استخراج موجودیت‌ها و روابط
- کشیدن نمودار برای نمایش داده‌ها (اولویت بالا!)
- پاسخ‌دهی بر اساس سابقه مکالمه
- ارجاع به پیام‌های قبلی

⭐ برای کشیدن نمودار، از فرمت زیر استفاده کنید (حتماً کامل و معتبر باشد):
```chart
{{
  "type": "bar",
  "title": "عنوان کامل نمودار",
  "labels": ["برچسب اول", "برچسب دوم", "برچسب سوم", "برچسب چهارم"],
  "datasets": [
    {{
      "label": "نام مجموعه داده",
      "data": [85, 70, 90, 65],
      "backgroundColor": ["rgba(239, 68, 68, 0.8)", "rgba(245, 158, 11, 0.8)", "rgba(16, 185, 129, 0.8)", "rgba(59, 130, 246, 0.8)"]
    }}
  ]
}}
```

⚠️ نکات فوق‌العاده مهم برای نمودار:
- حتماً از ```chart استفاده کنید (نه ```json)
- JSON کامل و معتبر باشد
- همه براکت‌ها و کاما‌ها درست باشند
- تعداد data با تعداد labels برابر باشد
- حتماً با ``` پایان یابد

🚫 مهم: نمودار نکشید اگر:
- سوال حقوقی، امنیتی، پلیسی، قضایی است
- داستان، سناریو، واقعه تعریف می‌کنید
- فقط توضیح متنی می‌خواهید
- هیچ عدد یا آمار واقعی وجود ندارد
- سوال درباره اشخاص، مکان‌ها، رویدادها است

✅ فقط نمودار بکشید اگر:
- کاربر صریحاً "نمودار" یا "چارت" گفته
- آمار و اعداد مشخص و واقعی دارید
- مقایسه عددی بین چندین مورد لازم است
- داده‌های قابل اندازه‌گیری وجود دارد

🔍 مثال‌های ممنوع:
- "شخصی وارد مغازه شده..." ← هیچ نمودار
- "تحلیل این موضوع..." ← هیچ نمودار
- "بررسی این مورد..." ← هیچ نمودار

❌ اشتباه: ```json
✅ درست: ```chart

انواع نمودار:
- "bar": نمودار میله‌ای (برای مقایسه)
- "line": نمودار خطی (برای روند)
- "pie": نمودار دایره‌ای (برای درصدها)
- "doughnut": نمودار حلقه‌ای (برای نسبت‌ها)

{history_context}"""

		# Check if user is asking about the AI assistant
		ai_question_keywords = [
			'تو کی هستی', 'تو کجا توسعه پیدا کردی', 'چه کسی نوشته ات', 'چه کسی توسعه داده ات',
			'کجا آموزش دیده ای', 'توسعه دهنده تو کیست', 'نویسنده تو کیست', 'چه کسی تو را ساخته',
			'نام تو چیست', 'اسم تو چیه', 'چی صدات کنم', 'Mentora', 'Mentora',
			'who are you', 'who created you', 'who developed you', 'who wrote you',
			'where were you developed', 'where were you trained', 'what is your name'
		]
		is_ai_question = any(keyword in req.message.lower() for keyword in ai_question_keywords)
		
		if is_ai_question:
			ai_response = get_system_identity_response()
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
		
		# Adjust parameters based on conversation complexity and question type
		temperature = 0.7
		max_tokens = 1024  # Increased default for better responses
		
		# Check if user is asking for detailed explanation
		detailed_request_keywords = [
			'توضیح دهید', 'توضیح بده', 'شرح دهید', 'تفصیل', 'کامل توضیح',
			'به طور کامل', 'مفصل', 'جزئیات', 'با جزئیات', 'دقیق توضیح',
			'explain in detail', 'detailed explanation', 'comprehensive'
		]
		
		needs_detailed_response = any(keyword in req.message.lower() for keyword in detailed_request_keywords)
		is_complex_question = len(req.message) > 100  # Long questions usually need long answers
		
		if needs_detailed_response or is_complex_question:
			max_tokens = 2048
			print("📝 Detailed response requested - increasing max tokens")
		
		if req.message_history and len(req.message_history) > 10:
			# For long conversations, use lower temperature for consistency
			temperature = 0.5
			max_tokens = max(max_tokens, 2048)  # Ensure at least 2048 for long conversations
			print("📝 Adjusting parameters for long conversation")
		elif req.message_history and len(req.message_history) > 5:
			# For medium conversations, increase tokens moderately
			max_tokens = max(max_tokens, 1536)
			print("📝 Adjusting parameters for medium conversation")
		
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
		import json
		
		# Enhanced chart pattern to handle incomplete charts
		chart_pattern = r'```chart\s*\n(.*?)(?:\n```|$)'
		chart_match = re.search(chart_pattern, clean_response, re.DOTALL)
		
		if chart_match:
			chart_json = chart_match.group(1).strip()
			print(f"🔍 Found chart block: {chart_json[:200]}...")
			
			try:
				# Try to parse as-is first
				chart_data = json.loads(chart_json)
				print(f"✅ Chart JSON parsed successfully")
				
			except json.JSONDecodeError as e:
				print(f"⚠️ Chart JSON parsing failed: {e}")
				print(f"📄 Full chart JSON content: {chart_json}")
				print(f"🔧 Attempting to fix incomplete chart JSON...")
				
				# Try to fix common issues
				fixed_json = fix_incomplete_chart_json(chart_json)
				if fixed_json:
					try:
						chart_data = json.loads(fixed_json)
						print(f"✅ Fixed chart JSON parsed successfully")
						print(f"🔧 Fixed JSON: {fixed_json}")
					except json.JSONDecodeError as e2:
						print(f"❌ Even fixed JSON failed to parse: {e2}")
						print(f"❌ Fixed JSON was: {fixed_json}")
						chart_data = None
				else:
					chart_data = None
			
			# Validate chart data structure
			if chart_data:
				print(f"🔍 Raw chart data before validation: {chart_data}")
				validated_chart_data = validate_and_complete_chart_data(chart_data)
				if validated_chart_data:
					chart_data = validated_chart_data
					print(f"📊 Valid chart data extracted: {chart_data.get('type', 'unknown')} chart with {len(chart_data.get('labels', []))} data points")
					print(f"📊 Final chart data: {chart_data}")
					# Remove chart block from response text
					clean_response = re.sub(chart_pattern, '', clean_response, flags=re.DOTALL).strip()
				else:
					print(f"❌ Chart data validation failed")
					chart_data = None
			else:
				print(f"❌ No valid chart data could be extracted")
		else:
			print(f"🔍 No chart block found in response")

		# Log chat to Elasticsearch (best-effort)
		try:
			es_target_index = getattr(req, 'es_index', None) or None
			esmod.log_chat({
				"language": language,
				"domain": domain,
				"model": model_name,
				"analysisMode": analysis_mode,
				"user_message": req.message,
				"assistant_message": clean_response,
				"has_chart": bool(chart_data),
				"chart_type": chart_data.get("type") if chart_data else None,
				"tokens": len(clean_response),
			}, index=es_target_index)
		except Exception:
			pass

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
		print(f"❌ Chat processing failed: {str(e)}")
		raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@app.post("/api/chat-speech-to-text", response_model=SpeechToTextResponse)
async def chat_speech_to_text(
	audio_file: UploadFile = File(...),
	language: str = Form("fa"),
	use_hybrid: bool = Form(True),
	model_preference: str = Form("auto", alias="model_preference")
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
	model_preference: str = Form("auto", alias="model_preference")
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
