"""
OpenRouter Provider Adapter.
Handles completions for free-tier models (Google Gemini 2.5 Flash, DeepSeek R1).
"""

import requests
from typing import Dict, Any, Optional
from app.core.constants import OPENROUTER_CHAT_URL, OPENROUTER_MODEL_ALIASES, OPENROUTER_PDF_MODEL


class OpenRouterAdapter:
    """Adapter for interacting with OpenRouter API."""

    def __init__(self):
        self.endpoint = OPENROUTER_CHAT_URL

    def resolve_model(self, model_id: str) -> str:
        """Resolves model aliases to active OpenRouter model identifier."""
        clean = (model_id or "").strip()
        for alias, target in OPENROUTER_MODEL_ALIASES.items():
            if clean == alias or alias in clean:
                return target
        return OPENROUTER_PDF_MODEL

    def complete(
        self,
        prompt: str,
        api_key: str,
        model_id: str = OPENROUTER_PDF_MODEL,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """Executes completion against OpenRouter API."""
        if not api_key:
            return {"success": False, "content": None, "error": "OpenRouter API key not provided", "status_code": 401}

        resolved_model = self.resolve_model(model_id)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000"
        }

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": resolved_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            resp = requests.post(self.endpoint, headers=headers, json=payload, timeout=60)

            # Dynamically push response headers to live quota tracker
            try:
                from app.core.quota_tracker import quota_tracker
                quota_tracker.update_live_headers("openrouter", resp.headers)
            except Exception:
                pass

            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                return {
                    "success": True,
                    "content": content,
                    "model": resolved_model,
                    "error": None,
                    "status_code": 200
                }
            elif resp.status_code == 429:
                return {
                    "success": False,
                    "content": (
                        "⚠️ OpenRouter rate limit reached. Please switch to another model "
                        "(e.g., Groq Qwen 3.8 27B or Local Ollama) using the Model Selector dropdown above."
                    ),
                    "model": resolved_model,
                    "error": f"OpenRouter Rate Limit Exceeded (HTTP 429): {resp.text[:120]}",
                    "status_code": 429
                }
            else:
                return {
                    "success": False,
                    "content": None,
                    "model": resolved_model,
                    "error": f"OpenRouter API Error (HTTP {resp.status_code}): {resp.text[:150]}",
                    "status_code": resp.status_code
                }

        except Exception as e:
            return {
                "success": False,
                "content": None,
                "model": resolved_model,
                "error": f"OpenRouter Connection Error: {str(e)}",
                "status_code": 500
            }


openrouter_adapter = OpenRouterAdapter()
