"""
Groq Provider Adapter.
Handles fast LPU inference and extracts live rate-limit response headers.
"""

import time
import requests
from typing import Dict, Any, Optional
from app.core.constants import GROQ_CHAT_URL, GROQ_MODEL_ALIASES, GROQ_DEFAULT_MODEL


class GroqAdapter:
    """Adapter for interacting with Groq Cloud API."""

    def __init__(self):
        self.endpoint = GROQ_CHAT_URL

    def resolve_model(self, model_id: str) -> str:
        """Resolves model aliases to active Groq model names."""
        clean = (model_id or "").strip()
        for alias, target in GROQ_MODEL_ALIASES.items():
            if clean == alias or alias in clean:
                return target
        return GROQ_DEFAULT_MODEL

    def complete(
        self,
        prompt: str,
        api_key: str,
        model_id: str = GROQ_DEFAULT_MODEL,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """
        Executes completion against Groq Cloud API.
        Extracts live rate limit headers and passes them to quota_tracker.
        """
        if not api_key:
            return {"success": False, "content": None, "error": "Groq API key not provided", "status_code": 401}

        resolved_model = self.resolve_model(model_id)
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        messages = []
        # Groq free tier limit is strictly 8,000 Tokens Per Minute (TPM).
        # We ensure: prompt tokens <= 2,200, output tokens <= 1,024 -> Total <= 3,200 tokens per request.
        # This preserves over 4,800 tokens for follow-up questions within the same 60-second window.
        MAX_SAFE_PROMPT_CHARS = 8000  # ~2,200 tokens
        safe_prompt = prompt or ""

        # Check live remaining tokens from recent Groq responses
        try:
            from app.core.quota_tracker import quota_tracker
            live_groq = quota_tracker._live_limits.get("groq", {})
            rem_tokens = live_groq.get("remaining_tokens")
            if rem_tokens is not None and rem_tokens < 3500:
                # Groq rolling window is partially depleted; tighten prompt further to fit remaining budget
                MAX_SAFE_PROMPT_CHARS = 4500
        except Exception:
            pass

        if len(safe_prompt) > MAX_SAFE_PROMPT_CHARS:
            half = MAX_SAFE_PROMPT_CHARS // 2
            safe_prompt = safe_prompt[:half] + "\n\n[...context condensed for Groq token rate optimization...]\n\n" + safe_prompt[-half:]

        if system_instruction:
            safe_sys = system_instruction[:2500] if len(system_instruction) > 2500 else system_instruction
            messages.append({"role": "system", "content": safe_sys})
        messages.append({"role": "user", "content": safe_prompt})

        # Estimate prompt tokens roughly (1 token ~= 3.5 chars)
        prompt_chars = sum(len(m.get("content", "")) for m in messages)
        estimated_prompt_tokens = int(prompt_chars / 3.5)
        # Cap max_tokens to 1024 max (384 min) so prompt + completion stays well below 3,500 tokens
        safe_max_tokens = max(256, min(max_tokens, 1024, 7000 - estimated_prompt_tokens))

        payload = {
            "model": resolved_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": safe_max_tokens
        }

        try:
            resp = requests.post(self.endpoint, headers=headers, json=payload, timeout=45)

            # Dynamically push response headers into live quota tracker
            try:
                from app.core.quota_tracker import quota_tracker
                quota_tracker.update_live_headers("groq", resp.headers)
            except Exception:
                pass

            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                content = choices[0].get("message", {}).get("content", "") if choices else ""
                return {
                    "success": True,
                    "content": content,
                    "model": resolved_model,
                    "error": None,
                    "status_code": 200
                }
            elif resp.status_code == 429:
                # Attempt a fast 2-second backoff retry with ultra-condensed prompt & 384 token budget
                time.sleep(2.0)
                # Condense retry message to ~3,000 chars so entire request is only ~1,200 tokens
                retry_messages = []
                if system_instruction:
                    retry_messages.append({"role": "system", "content": system_instruction[:1000]})
                retry_prompt = prompt[-3000:] if len(prompt or "") > 3000 else (prompt or "")
                retry_messages.append({"role": "user", "content": retry_prompt})

                payload["messages"] = retry_messages
                payload["max_tokens"] = 384
                try:
                    retry_resp = requests.post(self.endpoint, headers=headers, json=payload, timeout=30)
                    if retry_resp.status_code == 200:
                        try:
                            from app.core.quota_tracker import quota_tracker
                            quota_tracker.update_live_headers("groq", retry_resp.headers)
                        except Exception:
                            pass
                        data = retry_resp.json()
                        choices = data.get("choices", [])
                        content = choices[0].get("message", {}).get("content", "") if choices else ""
                        return {
                            "success": True,
                            "content": content,
                            "model": resolved_model,
                            "error": None,
                            "status_code": 200
                        }
                except Exception:
                    pass

                return {
                    "success": False,
                    "content": (
                        "⚠️ Groq rate limit reached. Please switch to another model "
                        "(e.g., OpenRouter Gemini 2.5 Flash, DeepSeek R1, or Local Ollama) "
                        "using the Model Selector dropdown above."
                    ),
                    "model": resolved_model,
                    "error": f"Groq Rate Limit Exceeded (HTTP 429): {resp.text[:120]}",
                    "status_code": 429
                }
            else:
                return {
                    "success": False,
                    "content": None,
                    "model": resolved_model,
                    "error": f"Groq API Error (HTTP {resp.status_code}): {resp.text[:150]}",
                    "status_code": resp.status_code
                }

        except Exception as e:
            return {
                "success": False,
                "content": None,
                "model": resolved_model,
                "error": f"Groq Connection Error: {str(e)}",
                "status_code": 500
            }


groq_adapter = GroqAdapter()
