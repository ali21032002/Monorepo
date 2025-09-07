import os

# Backend configuration for local Ollama + Gemma3:4b
OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "gemma3:4b")
REQUEST_TIMEOUT_SECONDS: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "120"))
TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0"))
MAX_OUTPUT_TOKENS: int = int(os.getenv("MAX_OUTPUT_TOKENS", "1024"))

# Input chunking & context window
NUM_CTX: int = int(os.getenv("NUM_CTX", os.getenv("CONTEXT_WINDOW", "4096")))
MAX_INPUT_CHARS: int = int(os.getenv("MAX_INPUT_CHARS", "12000"))
CHUNK_OVERLAP_CHARS: int = int(os.getenv("CHUNK_OVERLAP_CHARS", "200"))
MAX_CHUNKS: int = int(os.getenv("MAX_CHUNKS", "8"))

# CORS
ALLOW_ORIGINS = os.getenv("ALLOW_ORIGINS", "*").split(",")
ALLOW_CREDENTIALS = True
ALLOW_METHODS = ["*"]
ALLOW_HEADERS = ["*"]
