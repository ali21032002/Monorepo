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
		return client.chat(
			model=model,
			messages=messages,
			options={
				"temperature": temperature,
				"num_predict": max_output_tokens,
				"num_ctx": effective_num_ctx,
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
