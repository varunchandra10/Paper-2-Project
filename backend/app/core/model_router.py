import os
import ollama
from typing import Dict, Any, List, Optional
from app.core.config import settings


class ModelRouter:
    """Dynamic Ollama model router selecting optimal models based on task type."""

    def __init__(self, host: str = settings.OLLAMA_HOST):
        self.host = host
        self.client = ollama.Client(host=host)

    def get_available_models(self) -> List[str]:
        """Fetches list of downloaded Ollama models."""
        try:
            res = self.client.list()
            models = res.get("models", [])
            return [m.get("name") for m in models if isinstance(m, dict) and "name" in m]
        except Exception as e:
            print(f"[MODEL_ROUTER WARN] Failed to fetch Ollama model list ({e}), returning default fallback.")
            return [settings.DEFAULT_MODEL]

    def select_model_for_task(self, task_type: str, preferred_model: Optional[str] = None) -> str:
        """Selects the best available model based on task requirements."""
        if preferred_model:
            return preferred_model

        available = self.get_available_models()
        if not available:
            return settings.DEFAULT_MODEL

        # Priority routing tables
        if task_type in ["code_gen", "syntax_check", "static_check"]:
            for candidate in ["qwen2.5-coder:1.5b", "qwen2.5-coder", "codellama", "deepseek-coder"]:
                if any(candidate in m.lower() for m in available):
                    return candidate

        if task_type in ["reasoning", "extraction", "decomposition"]:
            for candidate in ["llama3.2:1b", "llama3", "mistral", "qwen2.5"]:
                if any(candidate in m.lower() for m in available):
                    return candidate

        return available[0]
