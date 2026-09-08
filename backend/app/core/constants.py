"""
Centralized Constants for Paper-2-Project Backend.

All external API endpoints, provider gateways, active model identifiers,
and baseline fallback rate-limit thresholds are consolidated here.
"""

# =====================================================================
# Provider API Gateways and Endpoints
# =====================================================================
GROQ_CHAT_URL: str = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODELS_URL: str = "https://api.groq.com/openai/v1/models"

OPENROUTER_CHAT_URL: str = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_AUTH_URL: str = "https://openrouter.ai/api/v1/auth/key"

HUGGINGFACE_CHAT_URL: str = "https://router.huggingface.co/v1/chat/completions"
HUGGINGFACE_WHOAMI_URL: str = "https://huggingface.co/api/whoami-v2"

GEMINI_BASE_URL: str = "https://generativelanguage.googleapis.com/v1beta/models"

OLLAMA_DEFAULT_HOST: str = "http://localhost:11434"
OLLAMA_TAGS_ENDPOINT: str = "/api/tags"
OLLAMA_GENERATE_ENDPOINT: str = "/api/generate"

# =====================================================================
# Active Model Identifiers
# =====================================================================
# Frontend Selectable Groq Models (Fast conversational chat & Q&A)
GROQ_DEFAULT_MODEL: str = "qwen/qwen3.8-27b"
GROQ_SECONDARY_MODEL: str = "openai/gpt-oss-120b"

# Frontend Selectable OpenRouter Models (Free tier chat & reasoning)
OPENROUTER_PDF_MODEL: str = "google/gemini-2.5-flash"
OPENROUTER_REASONING_MODEL: str = "deepseek/deepseek-r1:free"

# Backend Autonomous Dual Code Engine Models (Invoked ONLY on code requests)
BACKEND_GEMINI_MODEL: str = "gemini-2.0-flash"
BACKEND_HF_CODER_MODEL: str = "Qwen/Qwen2.5-Coder-32B-Instruct"

# Local Offline Model
OLLAMA_DEFAULT_MODEL: str = "qwen2.5-coder:1.5b"

# =====================================================================
# Model Mappings & Aliases
# =====================================================================
GROQ_MODEL_ALIASES = {
    "qwen/qwen3.8-27b": "qwen/qwen3.8-27b",
    "qwen": "qwen/qwen3.8-27b",
    "qwen3.8": "qwen/qwen3.8-27b",
    "openai/gpt-oss-120b": "openai/gpt-oss-120b",
    "gpt-oss": "openai/gpt-oss-120b",
    # Legacy alias support to map to active Groq model
    "llama-3.3": "qwen/qwen3.8-27b",
    "llama-3.3-70b": "qwen/qwen3.8-27b",
    "llama-3.3-70b-versatile": "qwen/qwen3.8-27b",
}

OPENROUTER_MODEL_ALIASES = {
    "google/gemini-2.5-flash": "google/gemini-2.5-flash",
    "gemini-2.5": "google/gemini-2.5-flash",
    "deepseek/deepseek-r1:free": "deepseek/deepseek-r1:free",
    "deepseek-r1": "deepseek/deepseek-r1:free",
}

# =====================================================================
# Initial Fallback Quota Thresholds
# (Dynamically overridden as soon as live API headers/telemetry are received)
# =====================================================================
INITIAL_GROQ_LIMIT_REQUESTS: int = 1000
INITIAL_GROQ_LIMIT_TOKENS: int = 8000
INITIAL_GROQ_MINUTE_LIMIT: int = 30
INITIAL_GEMINI_DAILY_LIMIT: int = 1500
INITIAL_GEMINI_MINUTE_LIMIT: int = 15
INITIAL_OPENROUTER_DAILY_LIMIT: int = 200
INITIAL_OPENROUTER_MINUTE_LIMIT: int = 20
INITIAL_HF_DAILY_LIMIT: int = 5000
INITIAL_HF_MINUTE_LIMIT: int = 30

# =====================================================================
# Generic Pipeline & Synthesis Defaults
# =====================================================================
DEFAULT_HYPERPARAMETERS = {
    "learning_rate": "0.0001",
    "batch_size": "16",
    "optimizer": "AdamW"
}

DEFAULT_PIPELINE_FILES = [
    "config.py",
    "dataset.py",
    "models/network.py",
    "losses.py",
    "train.py",
    "evaluate.py"
]
