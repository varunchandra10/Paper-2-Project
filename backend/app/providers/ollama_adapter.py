"""
Local Ollama Provider Adapter.
Handles model discovery and local offline hardware inference.
"""

import ollama
from typing import Dict, Any, List, Optional
from app.core.constants import OLLAMA_DEFAULT_HOST, OLLAMA_DEFAULT_MODEL


class OllamaAdapter:
    """Adapter for interacting with local or remote Ollama daemon."""

    def __init__(self, default_host: str = OLLAMA_DEFAULT_HOST):
        self.default_host = default_host

    def get_available_models(self, candidate_hosts: Optional[List[str]] = None) -> List[str]:
        """Discovers running local models across provided candidate host URLs."""
        hosts = candidate_hosts or [self.default_host]
        seen = set()
        for host in hosts:
            if not host or host in seen:
                continue
            seen.add(host)
            try:
                client = ollama.Client(host=host)
                res = client.list()
                models = res.get("models", [])
                if isinstance(models, list):
                    names = []
                    for m in models:
                        if isinstance(m, dict):
                            names.append(m.get("name", ""))
                        elif hasattr(m, "model"):
                            names.append(getattr(m, "model", str(m)))
                    found = [n for n in names if n]
                    if found:
                        return found
            except Exception:
                continue
        return []

    def complete(
        self,
        prompt: str,
        model_id: str = OLLAMA_DEFAULT_MODEL,
        host: Optional[str] = None,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2
    ) -> Dict[str, Any]:
        """Executes completion against local Ollama instance."""
        target_host = host or self.default_host
        try:
            client = ollama.Client(host=target_host)
            full_prompt = f"{system_instruction}\n\n{prompt}" if system_instruction else prompt
            res = client.generate(
                model=model_id,
                prompt=full_prompt,
                options={"temperature": temperature}
            )
            response_text = res.get("response", "")
            return {
                "success": True,
                "content": response_text,
                "model": model_id,
                "error": None,
                "status_code": 200
            }
        except Exception as e:
            return {
                "success": False,
                "content": None,
                "model": model_id,
                "error": f"Ollama Connection Error: {str(e)}",
                "status_code": 500
            }


ollama_adapter = OllamaAdapter()
