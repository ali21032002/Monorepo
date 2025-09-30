import os
try:
    # Load environment from nearest .env (walk-up) or custom ENV_FILE
    from dotenv import load_dotenv, find_dotenv  # type: ignore
    _env_path = os.getenv("ENV_FILE") or find_dotenv(usecwd=True)
    if _env_path:
        load_dotenv(_env_path)
except Exception:
    # If python-dotenv is not available, just rely on OS env
    pass

# Backend configuration for local Ollama + Gemma3:4b
OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "gemma3:4b")
REQUEST_TIMEOUT_SECONDS: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "120"))
TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0"))
MAX_OUTPUT_TOKENS: int = int(os.getenv("MAX_OUTPUT_TOKENS", "2048"))

# Input chunking & context window
NUM_CTX: int = int(os.getenv("NUM_CTX", os.getenv("CONTEXT_WINDOW", "4096")))
MAX_INPUT_CHARS: int = int(os.getenv("MAX_INPUT_CHARS", "12000"))
CHUNK_OVERLAP_CHARS: int = int(os.getenv("CHUNK_OVERLAP_CHARS", "200"))
MAX_CHUNKS: int = int(os.getenv("MAX_CHUNKS", "8"))

# Optional Elasticsearch integration
ES_ENABLED: bool = os.getenv("ES_ENABLED", "false").lower() in ("1", "true", "yes")
ES_HOST: str = os.getenv("ES_HOST", "http://localhost:9200")
ES_USERNAME: str = os.getenv("ES_USERNAME", "")
ES_PASSWORD: str = os.getenv("ES_PASSWORD", "")
ES_INDEX: str = os.getenv("ES_INDEX", "langextract-chats")
# Comma-separated list of indices for multi-index mode (optional)
ES_INDEXES: str = os.getenv("ES_INDEXES", "")

# Security/connection options (optional)
ES_API_KEY: str = os.getenv("ES_API_KEY", "")  # either base64 value or "id:key"
ES_BEARER_TOKEN: str = os.getenv("ES_BEARER_TOKEN", "")
ES_CLOUD_ID: str = os.getenv("ES_CLOUD_ID", "")
ES_TLS_VERIFY: bool = os.getenv("ES_TLS_VERIFY", "true").lower() not in ("0", "false", "no")
ES_CA_CERT: str = os.getenv("ES_CA_CERT", "")  # path to CA bundle or cert
ES_IGNORE_SSL_WARNINGS: bool = os.getenv("ES_IGNORE_SSL_WARNINGS", "false").lower() in ("1", "true", "yes")

# CORS
ALLOW_ORIGINS = os.getenv("ALLOW_ORIGINS", "*").split(",")
ALLOW_CREDENTIALS = True
ALLOW_METHODS = ["*"]
ALLOW_HEADERS = ["*"]
