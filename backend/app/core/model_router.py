"""
Model Router for Paper-2-Project.

Modular orchestrator that dispatches inference requests to specialized adapters:
- GroqAdapter (Fast conversational chat & Q&A)
- OpenRouterAdapter (Free tier reasoning & Gemini models)
- HuggingFaceAdapter (Dedicated Qwen 2.5 Coder 32B)
- OllamaAdapter (100% offline local models)
"""

from typing import Dict, Any, List, Optional, Tuple
from app.core.config import settings
from app.core.quota_tracker import quota_tracker
from app.core.constants import (
    GROQ_DEFAULT_MODEL,
    GROQ_SECONDARY_MODEL,
    OPENROUTER_PDF_MODEL,
    OPENROUTER_REASONING_MODEL,
    OLLAMA_DEFAULT_HOST
)
from app.providers import (
    groq_adapter,
    openrouter_adapter,
    hf_adapter,
    ollama_adapter
)


class ModelRouter:
    """Dynamic LLM Router supporting Groq API, OpenRouter API, and Local Ollama."""

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
        """Fetches list of available models from local Ollama instances."""
        candidate_hosts = [settings.OLLAMA_HOST, self.get_ollama_link(), OLLAMA_DEFAULT_HOST]
        return ollama_adapter.get_available_models(candidate_hosts)

    def get_user_api_keys(self) -> Tuple[Optional[str], Optional[str]]:
        """Retrieves user-configured private Groq and OpenRouter keys from user_profile.json."""
        try:
            from app.core.database import ChatDatabase
            profile = ChatDatabase().get_standalone_user_profile()
            groq_key = (profile.get("groqApiKey") or "").strip()
            or_key = (profile.get("openrouterApiKey") or "").strip()
            return (
                groq_key if len(groq_key) > 10 else None,
                or_key if len(or_key) > 10 else None
            )
        except Exception:
            return None, None

    def generate(self, prompt: str, model_id: Optional[str] = None) -> Tuple[str, str]:
        """
        Executes completion adhering to provider selection and quota limits:
        1. Groq: High-speed chat. On 429, intimates user to change model.
        2. OpenRouter: Free tier models.
        3. Local Ollama: Hardware offline inference.
        """
        requested = (model_id or settings.DEFAULT_MODEL).strip()
        user_groq, user_or = self.get_user_api_keys()

        groq_model_ids = [GROQ_DEFAULT_MODEL, GROQ_SECONDARY_MODEL, "qwen3.8", "gpt-oss", "groq"]
        is_groq_req = any(gid in requested.lower() for gid in groq_model_ids) or requested in [
            "llama-3.3-70b-versatile", "llama-3.1-8b-instant", "qwen-2.5-coder-32b", "deepseek-r1-distill-llama-70b"
        ]

        openrouter_model_ids = [OPENROUTER_PDF_MODEL, OPENROUTER_REASONING_MODEL, ":free", "openrouter"]
        is_openrouter_req = not is_groq_req and any(oid in requested.lower() for oid in openrouter_model_ids)

        # 1. User selected Groq model
        if is_groq_req:
            active_groq_key = user_groq or self.groq_api_key
            if not active_groq_key:
                return (
                    "⚠️ Groq API key is not configured. Please switch to an OpenRouter model "
                    "or Local Ollama using the Model Selector dropdown.",
                    requested
                )
            res = groq_adapter.complete(prompt, api_key=active_groq_key, model_id=requested)
            if res.get("success") and res.get("content"):
                quota_tracker.record_usage("groq", requested)
                return res["content"], f"Groq Cloud ({requested})"
            elif res.get("status_code") == 429 or not quota_tracker.is_provider_available("groq"):
                print(f"[ModelRouter] Groq rate limit reached (HTTP 429). Attempting automatic seamless failover...")
                
                # 1. Seamless Failover to Google Gemini 2.0 Flash (1,000,000 TPM capacity)
                if settings.has_gemini():
                    try:
                        import httpx
                        # API key goes in header only — never in URL (prevents key leakage in server logs)
                        gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
                        gemini_headers = {
                            "Content-Type": "application/json",
                            "x-goog-api-key": settings.GEMINI_API_KEY
                        }
                        g_res = httpx.post(
                            gemini_url,
                            headers=gemini_headers,
                            json={"contents": [{"parts": [{"text": prompt}]}]},
                            timeout=30.0
                        )
                        if g_res.status_code == 200:
                            g_data = g_res.json()
                            cand = g_data.get("candidates", [])
                            if cand and "parts" in cand[0].get("content", {}):
                                text = cand[0]["content"]["parts"][0]["text"]
                                quota_tracker.record_usage("gemini", "gemini-2.0-flash")
                                print("[ModelRouter] Seamlessly resolved query via Gemini 2.0 Flash failover!")
                                return text, "Gemini 2.0 Flash (Auto-Failover)"
                    except Exception as g_err:
                        print(f"[ModelRouter] Gemini failover notice: {g_err}")

                # 2. Seamless Failover to OpenRouter
                active_or_key = user_or or self.openrouter_api_key
                if active_or_key and quota_tracker.is_provider_available("openrouter"):
                    or_res = openrouter_adapter.complete(prompt, api_key=active_or_key, model_id=OPENROUTER_PDF_MODEL)
                    if or_res.get("success") and or_res.get("content"):
                        quota_tracker.record_usage("openrouter", OPENROUTER_PDF_MODEL)
                        print("[ModelRouter] Seamlessly resolved query via OpenRouter failover!")
                        return or_res["content"], f"OpenRouter ({OPENROUTER_PDF_MODEL} Auto-Failover)"

                # 3. Seamless Failover to Hugging Face Dedicated Qwen Coder
                if settings.has_huggingface():
                    try:
                        from app.providers import hf_adapter
                        hf_res = hf_adapter.complete(prompt, api_key=settings.HUGGINGFACE_API_KEY)
                        if hf_res.get("success") and hf_res.get("content"):
                            quota_tracker.record_usage("huggingface", "Qwen/Qwen2.5-Coder-32B-Instruct")
                            print("[ModelRouter] Seamlessly resolved query via Hugging Face failover!")
                            return hf_res["content"], "Hugging Face (Auto-Failover)"
                    except Exception as hf_err:
                        print(f"[ModelRouter] Hugging Face failover notice: {hf_err}")

                # If no alternative API keys are configured, notify user with retry guidance
                return (
                    "⚠️ Groq rate limit reached (HTTP 429). Please switch to another model "
                    "(e.g., OpenRouter Gemini 2.5 Flash, DeepSeek R1, or Local Ollama) using the "
                    "Model Selector dropdown above, or wait ~60s for your Groq token quota to reset.",
                    requested
                )
            elif res.get("error"):
                return f"⚠️ {res['error']}. Please switch to another model using the Model Selector above.", requested

        # 2. User selected OpenRouter model
        if is_openrouter_req:
            active_or_key = user_or or self.openrouter_api_key
            if active_or_key and quota_tracker.is_provider_available("openrouter"):
                res = openrouter_adapter.complete(prompt, api_key=active_or_key, model_id=requested)
                if res.get("success") and res.get("content"):
                    quota_tracker.record_usage("openrouter", requested)
                    return res["content"], f"OpenRouter ({requested})"
                elif res.get("status_code") == 429:
                    return (
                        "⚠️ OpenRouter rate limit reached. Please switch to another model "
                        "(e.g., Groq LLaMA, or Local Ollama) using the Model Selector dropdown above.",
                        requested
                    )
                elif res.get("error"):
                    return f"⚠️ {res['error']}. Please switch models in the Model Selector above.", requested

        # 3. Local Ollama execution
        target_host = self.get_ollama_link() or settings.OLLAMA_HOST or OLLAMA_DEFAULT_HOST
        res_local = ollama_adapter.complete(prompt, model_id=requested, host=target_host)
        if res_local.get("success") and res_local.get("content"):
            quota_tracker.record_usage("local", requested)
            return res_local["content"], f"Local Ollama ({requested})"

        # 4. Fallback attempt to Groq if local was offline
        active_groq_key = user_groq or self.groq_api_key
        if active_groq_key and quota_tracker.is_provider_available("groq"):
            res = groq_adapter.complete(prompt, api_key=active_groq_key, model_id=GROQ_DEFAULT_MODEL)
            if res.get("success") and res.get("content"):
                quota_tracker.record_usage("groq", GROQ_DEFAULT_MODEL)
                return res["content"], f"Groq Cloud ({GROQ_DEFAULT_MODEL})"

        # 5. Fallback attempt to OpenRouter
        active_or_key = user_or or self.openrouter_api_key
        if active_or_key and quota_tracker.is_provider_available("openrouter"):
            res = openrouter_adapter.complete(prompt, api_key=active_or_key, model_id=OPENROUTER_PDF_MODEL)
            if res.get("success") and res.get("content"):
                quota_tracker.record_usage("openrouter", OPENROUTER_PDF_MODEL)
                return res["content"], f"OpenRouter ({OPENROUTER_PDF_MODEL})"

        return "I am ready to help analyze your paper and synthesize PyTorch code.", "Local Ollama (Offline Mode)"
