from typing import Any, Dict, List, Optional
import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

try:
	from ollama import Client
except Exception:  # pragma: no cover
	Client = None  # type: ignore


def chat_json(
	*,
	system_prompt: str,
	user_prompt: str,
	model: str,
	temperature: float = 0.0,
	max_output_tokens: int = 1024,
	request_timeout_seconds: Optional[int] = None,
	num_ctx: Optional[int] = None,
) -> str:
	"""Call Ollama chat and return raw content string.

	The prompt instructs the model to output compact JSON only.
	"""
	host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
	if Client is None:
		raise RuntimeError("ollama Python package is not installed")
	client = Client(host=host)

	messages: List[Dict[str, str]] = [
		{"role": "system", "content": system_prompt},
		{"role": "user", "content": user_prompt},
	]

 
	effective_timeout = (
		int(request_timeout_seconds)
		if request_timeout_seconds is not None
		else int(os.getenv("REQUEST_TIMEOUT_SECONDS", "120"))
	)
	effective_num_ctx = (
		int(num_ctx)
		if num_ctx is not None
		else int(os.getenv("NUM_CTX", os.getenv("CONTEXT_WINDOW", "4096")))
	)

	def _do_chat() -> Dict[str, Any]:
		# Adjust context window based on message count
		adjusted_num_ctx = effective_num_ctx
		if len(messages) > 15:
			# Increase context window for long conversations
			adjusted_num_ctx = min(effective_num_ctx * 2, 8192)  # Cap at 8K
			print(f"📝 Adjusted context window to {adjusted_num_ctx} for long conversation")
		
		return client.chat(
			model=model,
			messages=messages,
			options={
				"temperature": temperature,
				"num_predict": max_output_tokens,
				"num_ctx": adjusted_num_ctx,
			},
		)

	with ThreadPoolExecutor(max_workers=1) as executor:
		future = executor.submit(_do_chat)
		try:
			resp: Dict[str, Any] = future.result(timeout=effective_timeout)
		except FuturesTimeout:
			future.cancel()
			raise RuntimeError(f"Ollama chat timed out after {effective_timeout}s")

	message = resp.get("message") or {}
	content: str = message.get("content", "{}")
	return content


def chat_conversational(
	*,
	system_prompt: str,
	user_message: str,
	model: str,
	message_history: Optional[List[Dict[str, str]]] = None,
	temperature: float = 0.0,
	max_output_tokens: int = 1024,
	request_timeout_seconds: Optional[int] = None,
	num_ctx: Optional[int] = None,
) -> str:
	"""Call Ollama chat with conversation history and return response string.

	This function supports conversational chat with message history.
	"""
	host = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
	if Client is None:
		raise RuntimeError("ollama Python package is not installed")
	client = Client(host=host)

	# Build messages list with history
	messages: List[Dict[str, str]] = [
		{"role": "system", "content": system_prompt},
	]
	
	# Add message history if provided
	if message_history:
		print(f"📝 Adding {len(message_history)} history messages to context")
		# Validate and clean message history
		valid_history = []
		for msg in message_history:
			if isinstance(msg, dict) and "role" in msg and "content" in msg:
				if msg["role"] in ["user", "assistant"] and msg["content"].strip():
					valid_history.append({
						"role": msg["role"],
						"content": msg["content"].strip()
					})
		
		if valid_history:
			messages.extend(valid_history)
			print(f"📝 Added {len(valid_history)} valid history messages")
		else:
			print("📝 No valid history messages found")
	
	# Add current user message
	messages.append({"role": "user", "content": user_message})
	
	# Debug: Show final message structure
	print(f"📝 Final message structure: {len(messages)} total messages")
	for i, msg in enumerate(messages):
		print(f"  {i+1}. {msg['role']}: {msg['content'][:50]}...")
	
	# Validate message structure
	if len(messages) > 20:
		print(f"⚠️ Warning: Large message context ({len(messages)} messages) may affect performance")
	
	# Check for proper conversation flow
	user_count = sum(1 for msg in messages if msg['role'] == 'user')
	assistant_count = sum(1 for msg in messages if msg['role'] == 'assistant')
	print(f"📝 Message balance: {user_count} user, {assistant_count} assistant messages")
	
	# Check for conversation quality
	if user_count > 0 and assistant_count > 0:
		balance_ratio = user_count / assistant_count
		if balance_ratio > 2:
			print("⚠️ Warning: User messages significantly outnumber assistant messages")
		elif balance_ratio < 0.5:
			print("⚠️ Warning: Assistant messages significantly outnumber user messages")
		else:
			print("✅ Good conversation balance")
	
	# Check for important content
	all_content = " ".join([msg['content'] for msg in messages])
	if 'نام' in all_content or 'اسم' in all_content:
		print("📝 Context contains name/identity information")
	if 'مشکل' in all_content or 'خطا' in all_content:
		print("📝 Context contains problem/error information")
	if '؟' in all_content or '?' in all_content:
		print("📝 Context contains questions")

	effective_timeout = (
		int(request_timeout_seconds)
		if request_timeout_seconds is not None
		else int(os.getenv("REQUEST_TIMEOUT_SECONDS", "120"))
	)
	effective_num_ctx = (
		int(num_ctx)
		if num_ctx is not None
		else int(os.getenv("NUM_CTX", os.getenv("CONTEXT_WINDOW", "4096")))
	)

	def _do_chat() -> Dict[str, Any]:
		# Adjust context window based on message count
		adjusted_num_ctx = effective_num_ctx
		if len(messages) > 15:
			# Increase context window for long conversations
			adjusted_num_ctx = min(effective_num_ctx * 2, 8192)  # Cap at 8K
			print(f"📝 Adjusted context window to {adjusted_num_ctx} for long conversation")
		
		return client.chat(
			model=model,
			messages=messages,
			options={
				"temperature": temperature,
				"num_predict": max_output_tokens,
				"num_ctx": adjusted_num_ctx,
			},
		)

	with ThreadPoolExecutor(max_workers=1) as executor:
		future = executor.submit(_do_chat)
		try:
			resp: Dict[str, Any] = future.result(timeout=effective_timeout)
		except FuturesTimeout:
			future.cancel()
			raise RuntimeError(f"Ollama chat timed out after {effective_timeout}s")

	message = resp.get("message") or {}
	content: str = message.get("content", "")
	
	# Log response quality
	print(f"📝 Generated response: {len(content)} characters")
	if len(content) < 10:
		print("⚠️ Warning: Very short response from model")
	elif len(content) > 1000:
		print("📝 Long response from model")
	
	# Check if response seems to consider history
	if message_history and len(message_history) > 0:
		history_indicators = ['قبلاً', 'سابقاً', 'گفتم', 'گفتید', 'قبل', 'پیش', 'همان', 'همین']
		considers_history = any(indicator in content for indicator in history_indicators)
		if considers_history:
			print("✅ Model response appears to consider conversation history")
		else:
			print("⚠️ Model response may not be considering conversation history")
		
		# Check for specific references to previous messages
		has_specific_reference = any(
			msg['content'] in content or 
			(len(msg['content']) > 10 and msg['content'][:10] in content)
			for msg in message_history
		)
		if has_specific_reference:
			print("✅ Model response contains specific reference to previous message")
		
		# Check for continuity in conversation
		has_continuity = any(
			msg['role'] == 'user' and msg['content'].lower()[:5] in content.lower()
			for msg in message_history
		)
		if has_continuity:
			print("✅ Model response shows good conversation continuity")
		
		# Check for context awareness
		has_context_awareness = any(
			msg['role'] == 'assistant' and msg['content'].lower()[:5] in content.lower()
			for msg in message_history
		)
		if has_context_awareness:
			print("✅ Model response shows context awareness from previous assistant messages")
		
		# Overall conversation quality assessment
		quality_indicators = [
			considers_history,
			has_specific_reference,
			has_continuity,
			has_context_awareness
		]
		quality_score = sum(quality_indicators)
		print(f"📝 Model conversation quality score: {quality_score}/4")
		
		if quality_score >= 3:
			print("✅ Excellent model conversation quality")
		elif quality_score >= 2:
			print("✅ Good model conversation quality")
		elif quality_score >= 1:
			print("⚠️ Fair model conversation quality")
		else:
			print("⚠️ Poor model conversation quality - may not be considering history")
		
		# Store quality score for potential future use
		if quality_score < 2:
			print("⚠️ Consider improving conversation context or model parameters")
		
		# Log conversation summary for debugging
		print(f"📝 Model conversation summary: {len(message_history)} messages, quality: {quality_score}/4")
		if message_history:
			last_user_message = next((msg for msg in reversed(message_history) if msg['role'] == 'user'), None)
			last_assistant_message = next((msg for msg in reversed(message_history) if msg['role'] == 'assistant'), None)
			if last_user_message:
				print(f"📝 Last user message: \"{last_user_message['content'][:50]}...\"")
			if last_assistant_message:
				print(f"📝 Last assistant message: \"{last_assistant_message['content'][:50]}...\"")
		
		# Log current message for context
		print(f"📝 Current user message: \"{user_message[:50]}...\"")
		print(f"📝 Current model response: \"{content[:50]}...\"")
		
		# Log conversation flow for debugging
		print(f"📝 Model conversation flow: {len(message_history)} previous messages → current exchange")
		if message_history:
			user_messages = sum(1 for msg in message_history if msg['role'] == 'user')
			assistant_messages = sum(1 for msg in message_history if msg['role'] == 'assistant')
			print(f"📝 Previous flow: {user_messages} user messages, {assistant_messages} assistant messages")
		
		# Log conversation quality metrics
		print(f"📝 Model quality metrics: History consideration: {considers_history}, Specific refs: {has_specific_reference}, Continuity: {has_continuity}, Context awareness: {has_context_awareness}")
		
		# Log conversation health check
		health_check = {
			'has_history': len(message_history) > 0,
			'has_quality': quality_score >= 2,
			'has_continuity': has_continuity,
			'has_context': has_context_awareness
		}
		print(f"📝 Model conversation health check: {health_check}")
		
		if not health_check['has_history']:
			print("⚠️ No conversation history available")
		if not health_check['has_quality']:
			print("⚠️ Low model conversation quality detected")
		
		# Log conversation improvement suggestions
		if quality_score < 2:
			print("💡 Suggestions for better model conversation quality:")
			if not considers_history:
				print("  - Model may need better history context")
			if not has_specific_reference:
				print("  - Model may need to reference specific previous messages")
			if not has_continuity:
				print("  - Model may need better conversation continuity")
			if not has_context_awareness:
				print("  - Model may need better context awareness")
	
	return content