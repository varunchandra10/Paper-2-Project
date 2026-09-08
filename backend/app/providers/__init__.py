"""
Provider Adapters Package for Paper-2-Project Backend.
Modular adapters for Groq, OpenRouter, Hugging Face, and Local Ollama.
"""

from app.providers.groq_adapter import GroqAdapter, groq_adapter
from app.providers.openrouter_adapter import OpenRouterAdapter, openrouter_adapter
from app.providers.hf_adapter import HuggingFaceAdapter, hf_adapter
from app.providers.ollama_adapter import OllamaAdapter, ollama_adapter

__all__ = [
    "GroqAdapter", "groq_adapter",
    "OpenRouterAdapter", "openrouter_adapter",
    "HuggingFaceAdapter", "hf_adapter",
    "OllamaAdapter", "ollama_adapter"
]
