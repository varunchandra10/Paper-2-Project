"""
Hugging Face Provider Adapter.
Handles serverless router inference for Qwen 2.5 Coder 32B Instruct.
Supports both synchronous calls and asynchronous parallel execution for DualCodeEngine.
"""

import httpx
import requests
from typing import Dict, Any, Optional
from app.core.constants import HUGGINGFACE_CHAT_URL, BACKEND_HF_CODER_MODEL


class HuggingFaceAdapter:
    """Adapter for interacting with Hugging Face Serverless Router."""

    def __init__(self):
        self.endpoint = HUGGINGFACE_CHAT_URL

    def complete(
        self,
        prompt: str,
        api_key: str,
        model_id: str = BACKEND_HF_CODER_MODEL,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """Synchronous completion via requests."""
        if not api_key:
            return {"success": False, "content": None, "error": "Hugging Face API key not provided", "status_code": 401}

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            resp = requests.post(self.endpoint, headers=headers, json=payload, timeout=60)

            # Dynamically push response headers to live quota tracker
            try:
                from app.core.quota_tracker import quota_tracker
                quota_tracker.update_live_headers("huggingface", resp.headers)
            except Exception:
                pass

            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                return {
                    "success": True,
                    "content": content,
                    "model": model_id,
                    "error": None,
                    "status_code": 200
                }
            else:
                return {
                    "success": False,
                    "content": None,
                    "model": model_id,
                    "error": f"Hugging Face API Error (HTTP {resp.status_code}): {resp.text[:150]}",
                    "status_code": resp.status_code
                }
        except Exception as e:
            return {
                "success": False,
                "content": None,
                "model": model_id,
                "error": f"Hugging Face Connection Error: {str(e)}",
                "status_code": 500
            }

    async def complete_async(
        self,
        prompt: str,
        api_key: str,
        model_id: str = BACKEND_HF_CODER_MODEL,
        system_instruction: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """Asynchronous completion for parallel dual-engine execution."""
        if not api_key:
            return {"success": False, "content": None, "error": "Hugging Face API key not provided", "status_code": 401}

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model_id,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                resp = await client.post(self.endpoint, headers=headers, json=payload)

                # Dynamically push response headers to live quota tracker
                try:
                    from app.core.quota_tracker import quota_tracker
                    quota_tracker.update_live_headers("huggingface", resp.headers)
                except Exception:
                    pass

                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    return {
                        "success": True,
                        "content": content,
                        "model": model_id,
                        "error": None,
                        "status_code": 200
                    }
                else:
                    return {
                        "success": False,
                        "content": None,
                        "model": model_id,
                        "error": f"Hugging Face API Error (HTTP {resp.status_code}): {resp.text[:150]}",
                        "status_code": resp.status_code
                    }
        except Exception as e:
            return {
                "success": False,
                "content": None,
                "model": model_id,
                "error": f"Hugging Face Connection Error: {str(e)}",
                "status_code": 500
            }


hf_adapter = HuggingFaceAdapter()
