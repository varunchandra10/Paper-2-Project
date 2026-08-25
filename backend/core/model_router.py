import os
import requests
import ollama
from typing import List, Dict, Any, Tuple, Optional

# Load environment variables
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv(os.path.join(backend_dir, ".env"))

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


class ModelRouter:
    """Orchestrates Phase 10 Model Routing. Classifies tasks and routes them

    to optimal local/remote models with automatic cascading fallbacks.
    """

    def __init__(self, local_model: str = "qwen2.5-coder:1.5b"):
        self.local_model = local_model
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")

    def classify_task(self, query: str) -> str:
        """Day 39: Classifies the incoming query into one of six categories."""
        prompt = f"""You are a task classifier. Categorize the user's request into one of the following exact categories:
- 'explanation': simple conceptual explanations or general definitions.
- 'extraction': requesting data, metadata, or hyperparameter details.
- 'reasoning': architectural decisions, structural math reasoning, or feasibility analysis.
- 'code_generation': writing new dataset loaders, model components, or code scripts.
- 'debugging': fixing syntax errors, importing issues, or python exceptions.
- 'summarization': compiling logs, reports, or history blocks.

Return ONLY the category name in lowercase with no quotes or additional text.

Request: "{query}"
Category:"""
        try:
            response = ollama.generate(model=self.local_model, prompt=prompt)
            category = response.get("response", "").strip().lower()
            # Clean up punctuation/quotes if any
            category = category.replace('"', '').replace("'", "").replace(".", "")
            
            valid_categories = ["explanation", "extraction", "reasoning", "code_generation", "debugging", "summarization"]
            for valid in valid_categories:
                if valid in category:
                    return valid
            return "explanation"  # Default fallback
        except Exception as e:
            print(f"[ROUTER WARN] Task classification failed: {e}")
            return "explanation"

    def _route_groq(self, prompt: str, model: str) -> Optional[str]:
        """Queries the Groq API endpoint."""
        if not self.groq_api_key:
            return None
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2
        }
        try:
            resp = requests.post(url, headers=headers, json=data, timeout=10)
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].strip()
            print(f"[ROUTER WARN] Groq API returned status {resp.status_code}: {resp.text[:100]}")
            return None
        except Exception as e:
            print(f"[ROUTER WARN] Groq API call failed for model {model}: {e}")
            return None

    def _route_openrouter(self, prompt: str, model: str) -> Optional[str]:
        """Queries the OpenRouter API endpoint."""
        if not self.openrouter_api_key:
            return None
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8000"
        }
        data = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2
        }
        try:
            resp = requests.post(url, headers=headers, json=data, timeout=12)
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"].strip()
            print(f"[ROUTER WARN] OpenRouter API returned status {resp.status_code}: {resp.text[:100]}")
            return None
        except Exception as e:
            print(f"[ROUTER WARN] OpenRouter API call failed for model {model}: {e}")
            return None

    def generate_routed_response(self, prompt: str, category: str) -> Tuple[str, str]:
        """Day 40-41: Routes query and applies cascading fallback logic.

        Returns: (response_text, model_used_label)
        """
        # Local-First Routing Map (Day 40)
        local_categories = ["explanation", "extraction", "summarization"]
        if category in local_categories:
            try:
                resp = ollama.generate(model=self.local_model, prompt=prompt)
                return resp.get("response", "").strip(), f"Ollama ({self.local_model})"
            except Exception as e:
                print(f"[ROUTER WARN] Local Ollama generate failed: {e}")

        # Heavy / Complex Routing Chain (Day 41)
        # Try OpenRouter Primary first, then Secondary
        if self.openrouter_api_key:
            # Primary: Claude 3.5 Sonnet
            primary_or = "anthropic/claude-3.5-sonnet"
            res = self._route_openrouter(prompt, primary_or)
            if res:
                return res, f"OpenRouter ({primary_or})"
                
            # Secondary: Gemini 2.5 Flash
            secondary_or = "google/gemini-2.5-flash"
            res = self._route_openrouter(prompt, secondary_or)
            if res:
                return res, f"OpenRouter ({secondary_or})"

        # Try Groq Primary, then Secondary
        if self.groq_api_key:
            # Primary: Llama 3.3 70B
            primary_groq = "llama-3.3-70b-versatile"
            res = self._route_groq(prompt, primary_groq)
            if res:
                return res, f"Groq ({primary_groq})"
                
            # Secondary: Llama 3.1 8B
            secondary_groq = "llama-3.1-8b-instant"
            res = self._route_groq(prompt, secondary_groq)
            if res:
                return res, f"Groq ({secondary_groq})"

        # Local Fallback (Day 41)
        try:
            print("[ROUTER] Remote APIs unreachable/unauthorized. Engaging local fallback model...")
            resp = ollama.generate(model=self.local_model, prompt=prompt)
            return resp.get("response", "").strip(), f"Ollama Fallback ({self.local_model})"
        except Exception as e:
            return f"Error: All remote and local models failed to generate a response ({str(e)}).", "N/A"
