import os
import requests
import ollama
from typing import Dict, Any, List, Optional, Tuple
from app.core.config import settings


class ModelRouter:
    """Dynamic LLM Router supporting Groq API, OpenRouter API, and User-Configured Ollama Link."""

    def __init__(self, host: Optional[str] = None):
        self.custom_host = host
        self.groq_api_key = settings.GROQ_API_KEY if settings.has_groq() else None
        self.openrouter_api_key = settings.OPENROUTER_API_KEY if settings.has_openrouter() else None

    def get_ollama_link(self) -> str:
        """Retrieves user-configured Ollama link from storage/history/user_profile.json."""
        if self.custom_host and (self.custom_host.startswith("http://") or self.custom_host.startswith("https://")):
            return self.custom_host
        try:
            from app.core.database import ChatDatabase
            profile = ChatDatabase().get_standalone_user_profile()
            link = profile.get("ollamaLink", "").strip()
            if link and (link.startswith("http://") or link.startswith("https://")):
                return link
        except Exception:
            pass
        return ""

    def get_available_models(self) -> List[str]:
        """Fetches list of local Ollama models ONLY if user provided a valid, live ollamaLink."""
        host = self.get_ollama_link()
        if not host:
            return []

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
                return [n for n in names if n]
            return []
        except Exception as e:
            print(f"[MODEL_ROUTER WARN] Provided Ollama link '{host}' is not responding ({e}).")
            return []

    def _route_groq(self, prompt: str, model_id: str = "llama-3.3-70b") -> Optional[str]:
        """Executes completion against Groq Cloud API LPU endpoints."""
        if not self.groq_api_key:
            return None
            
        groq_model_map = {
            "llama-3.3-70b": "openai/gpt-oss-120b",
            "qwen-2.5-coder-32b": "qwen/qwen3.6-27b",
            "deepseek-r1": "openai/gpt-oss-120b",
            "deepseek-r1-distill": "openai/gpt-oss-120b",
            "gemini-2.0-flash": "groq/compound-mini"
        }
        target_model = groq_model_map.get(model_id, "openai/gpt-oss-120b")
        
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": target_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2
        }
        try:
            resp = requests.post(url, headers=headers, json=data, timeout=15)
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"].strip()
                if content:
                    return content
            print(f"[ROUTER WARN] Groq API returned status {resp.status_code}: {resp.text[:100]}")
            return None
        except Exception as e:
            print(f"[ROUTER WARN] Groq API call failed for model {target_model}: {e}")
            return None

    def _route_openrouter(self, prompt: str, model_id: str = "llama-3.3-70b") -> Optional[str]:
        """Executes completion against OpenRouter API endpoints."""
        if not self.openrouter_api_key:
            return None
            
        openrouter_model_map = {
            "llama-3.3-70b": "nvidia/nemotron-3-super-120b-a12b:free",
            "qwen-2.5-coder-32b": "nvidia/nemotron-3-super-120b-a12b:free",
            "deepseek-r1": "nvidia/nemotron-3-super-120b-a12b:free",
            "gemini-2.0-flash": "nvidia/nemotron-3-super-120b-a12b:free"
        }
        target_model = openrouter_model_map.get(model_id, "nvidia/nemotron-3-super-120b-a12b:free")
        
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000"
        }
        data = {
            "model": target_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2
        }
        try:
            resp = requests.post(url, headers=headers, json=data, timeout=15)
            if resp.status_code == 200:
                content = resp.json()["choices"][0]["message"]["content"].strip()
                if content:
                    return content
            print(f"[ROUTER WARN] OpenRouter API returned status {resp.status_code}: {resp.text[:100]}")
            return None
        except Exception as e:
            print(f"[ROUTER WARN] OpenRouter API call failed for model {target_model}: {e}")
            return None

    def generate(self, prompt: str, model_id: Optional[str] = None) -> Tuple[str, str]:
        """
        Executes completion with 100% Local-First priority:
        1. Local Ollama (using settings.OLLAMA_HOST or user-configured link)
        2. Groq Cloud API (fallback if local Ollama fails/unresponsive)
        3. OpenRouter API (fallback if Groq fails)
        
        Returns: (generated_text, model_label_used)
        """
        requested = model_id or settings.DEFAULT_MODEL
        
        # 1. Primary: Local Ollama (100% Local LLM Execution)
        ollama_hosts = [
            settings.OLLAMA_HOST,
            self.get_ollama_link(),
            "http://localhost:11434"
        ]
        seen_hosts = set()
        for host in ollama_hosts:
            if not host or host in seen_hosts:
                continue
            seen_hosts.add(host)
            try:
                client = ollama.Client(host=host)
                res = client.generate(model=requested, prompt=prompt)
                output = res.get("response", "").strip()
                if output:
                    return output, f"Local Ollama ({requested})"
            except Exception as e:
                pass

        # 2. Secondary Fallback: Groq Cloud API LPU (if API key available)
        if self.groq_api_key:
            res = self._route_groq(prompt, requested)
            if res:
                return res, f"Groq API ({requested})"

        # 3. Tertiary Fallback: OpenRouter API (if API key available)
        if self.openrouter_api_key:
            res = self._route_openrouter(prompt, requested)
            if res:
                return res, f"OpenRouter API ({requested})"

        return "I am ready to help analyze your paper and synthesize PyTorch code.", settings.DEFAULT_MODEL
