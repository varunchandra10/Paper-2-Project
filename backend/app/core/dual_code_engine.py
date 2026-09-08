"""
Dedicated Autonomous Backend Dual Code Engine.

Executes parallel code synthesis using Google Gemini (deep paper context & math)
and Hugging Face Qwen 2.5 Coder 32B (idiomatic PyTorch specialist).
Prompts are loaded exclusively from app.core.prompts.
Constants and endpoints are loaded from app.core.constants.
Enforces AST syntax validation, security checks, and cross-engine failover.
"""

import ast
import asyncio
import httpx
from typing import Dict, Any, Optional, Tuple
from app.core.config import settings
from app.core.quota_tracker import quota_tracker
from app.core.constants import (
    GEMINI_BASE_URL,
    BACKEND_GEMINI_MODEL,
    BACKEND_HF_CODER_MODEL
)
from app.core.prompts import (
    CODE_SYNTHESIS_SYSTEM_PROMPT,
    build_code_synthesis_user_prompt
)
from app.providers.hf_adapter import hf_adapter


def extract_python_code(raw_text: str) -> str:
    """Extracts clean python code from markdown blocks or raw text."""
    if not raw_text:
        return ""
    if "```python" in raw_text:
        parts = raw_text.split("```python")
        if len(parts) > 1:
            return parts[-1].split("```")[0].strip()
    elif "```" in raw_text:
        parts = raw_text.split("```")
        if len(parts) >= 3:
            return parts[1].strip()
    return raw_text.strip()


def validate_code_syntax(code: str) -> Tuple[bool, Optional[str]]:
    """Validates Python syntax via ast.parse and enforces security constraints."""
    if not code or not code.strip():
        return False, "Empty code snippet"
    try:
        tree = ast.parse(code)
        # Security check: verify no banned primitives
        from app.core.code_verifier import code_verifier
        safety = code_verifier.check_banned_primitives(tree)
        if not safety.get("safe", True):
            return False, f"Security violation: {safety.get('reason')}"
        return True, None
    except SyntaxError as e:
        return False, f"SyntaxError on line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"AST Error: {str(e)}"


class DualCodeEngine:
    """
    Dedicated Backend Code Synthesis Engine:
    Executes parallel code generation using Google Gemini (1M context) and Hugging Face Qwen 2.5 Coder 32B.
    Completely isolated from user chat quotas (does not consume Groq or OpenRouter limits).
    Enforces AST syntax validation and cross-engine failover.
    """

    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        hf_api_key: Optional[str] = None,
        gemini_model: Optional[str] = None,
        hf_model: Optional[str] = None,
    ):
        self.gemini_api_key = gemini_api_key or settings.GEMINI_API_KEY
        raw_gem = gemini_model or settings.GEMINI_MODEL or BACKEND_GEMINI_MODEL
        self.gemini_model = BACKEND_GEMINI_MODEL if ("2.0-flash" in raw_gem or "2.5-flash" in raw_gem) else raw_gem
        self.hf_api_key = hf_api_key or settings.HUGGINGFACE_API_KEY
        self.hf_model = hf_model or BACKEND_HF_CODER_MODEL

    async def generate_gemini(self, prompt: str, system_instruction: str = "") -> Dict[str, Any]:
        """Queries Google Gemini API for deep paper-contextualized PyTorch synthesis."""
        if not self.gemini_api_key or len(self.gemini_api_key) < 10:
            return {
                "code": "",
                "raw": "",
                "valid": False,
                "model": self.gemini_model,
                "provider": "Google Gemini",
                "error": "GEMINI_API_KEY not configured"
            }

        url = f"{GEMINI_BASE_URL}/{self.gemini_model}:generateContent"

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 8192
            }
        }
        sys_inst = system_instruction or CODE_SYNTHESIS_SYSTEM_PROMPT
        payload["systemInstruction"] = {
            "parts": [{"text": sys_inst}]
        }

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.gemini_api_key
        }

        try:
            async with httpx.AsyncClient(timeout=35.0) as client:
                resp = await client.post(url, headers=headers, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        raw_text = "".join(p.get("text", "") for p in parts if "text" in p).strip()
                        quota_tracker.record_usage("gemini", self.gemini_model)
                        clean_code = extract_python_code(raw_text)
                        is_valid, syntax_err = validate_code_syntax(clean_code)
                        return {
                            "code": clean_code,
                            "raw": raw_text,
                            "valid": is_valid,
                            "syntax_error": syntax_err,
                            "model": self.gemini_model,
                            "provider": "Google Gemini 3.6 Flash",
                            "error": None if is_valid else syntax_err
                        }
                return {
                    "code": "",
                    "raw": "",
                    "valid": False,
                    "model": self.gemini_model,
                    "provider": "Google Gemini",
                    "error": f"HTTP {resp.status_code}: {resp.text[:120]}"
                }
        except Exception as e:
            return {
                "code": "",
                "raw": "",
                "valid": False,
                "model": self.gemini_model,
                "provider": "Google Gemini",
                "error": str(e)
            }

    async def generate_huggingface(self, prompt: str, system_instruction: str = "") -> Dict[str, Any]:
        """Queries Hugging Face Serverless Router for high-fidelity Qwen 2.5 Coder 32B PyTorch synthesis."""
        key = self.hf_api_key or settings.HUGGINGFACE_API_KEY
        if not key or len(key) < 5:
            return {
                "code": "",
                "raw": "",
                "valid": False,
                "model": self.hf_model,
                "provider": "Hugging Face",
                "error": "HUGGINGFACE_API_KEY not configured"
            }

        sys_inst = system_instruction or CODE_SYNTHESIS_SYSTEM_PROMPT
        res = await hf_adapter.complete_async(
            prompt=prompt,
            api_key=key,
            model_id=self.hf_model,
            system_instruction=sys_inst,
            temperature=0.2,
            max_tokens=8192
        )

        if res.get("success") and res.get("content"):
            raw_text = res["content"].strip()
            quota_tracker.record_usage("huggingface", self.hf_model)
            clean_code = extract_python_code(raw_text)
            is_valid, syntax_err = validate_code_syntax(clean_code)
            return {
                "code": clean_code,
                "raw": raw_text,
                "valid": is_valid,
                "syntax_error": syntax_err,
                "model": self.hf_model,
                "provider": "Hugging Face (Qwen 2.5 Coder 32B)",
                "error": None if is_valid else syntax_err
            }

        return {
            "code": "",
            "raw": "",
            "valid": False,
            "model": self.hf_model,
            "provider": "Hugging Face",
            "error": res.get("error", "HF synthesis failed")
        }

    async def generate_dual_candidates(
        self,
        prompt: str,
        system_instruction: str = ""
    ) -> Dict[str, Dict[str, Any]]:
        """
        Executes parallel calls to Google Gemini (Deep Context) and Hugging Face Qwen 2.5 Coder 32B (Code Specialist).
        Returns candidate dictionary: {'gemini': {...}, 'huggingface': {...}}
        """
        gemini_task = self.generate_gemini(prompt, system_instruction=system_instruction)
        hf_task = self.generate_huggingface(prompt, system_instruction=system_instruction) if settings.has_huggingface() else None

        if hf_task:
            gemini_res, hf_res = await asyncio.gather(gemini_task, hf_task, return_exceptions=False)
            return {
                "gemini": gemini_res,
                "huggingface": hf_res
            }
        else:
            gemini_res = await gemini_task
            return {
                "gemini": gemini_res
            }

    def generate_dual_candidates_sync(
        self,
        prompt: str,
        system_instruction: str = ""
    ) -> Dict[str, Dict[str, Any]]:
        """Synchronous wrapper for agent pipeline loops."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                    future = executor.submit(asyncio.run, self.generate_dual_candidates(prompt, system_instruction))
                    return future.result()
            else:
                return loop.run_until_complete(self.generate_dual_candidates(prompt, system_instruction))
        except Exception:
            return asyncio.run(self.generate_dual_candidates(prompt, system_instruction))

    async def repair_code_syntax(self, broken_code: str, error_msg: str) -> Tuple[str, str]:
        """Attempts an automatic 1-turn repair of Python syntax errors using the active LLM."""
        repair_prompt = (
            "You are an expert PyTorch code debugger. The following Python code produced a syntax error:\n\n"
            f"ERROR: {error_msg}\n\n"
            f"CODE TO FIX:\n```python\n{broken_code}\n```\n\n"
            "Fix the syntax error and return ONLY the complete, valid Python code enclosed in ```python ... ``` without explanation."
        )
        if settings.has_gemini():
            res = await self.generate_gemini(repair_prompt)
            if res.get("code") and validate_code_syntax(res["code"])[0]:
                return res["code"], "Google Gemini"
        if settings.has_huggingface():
            res = await self.generate_huggingface(repair_prompt)
            if res.get("code") and validate_code_syntax(res["code"])[0]:
                return res["code"], "Hugging Face"
        return "", ""

    def repair_code_syntax_sync(self, broken_code: str, error_msg: str) -> Tuple[str, str]:
        """Synchronous wrapper for 1-turn syntax repair."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    future = executor.submit(asyncio.run, self.repair_code_syntax(broken_code, error_msg))
                    return future.result()
            else:
                return loop.run_until_complete(self.repair_code_syntax(broken_code, error_msg))
        except Exception:
            return asyncio.run(self.repair_code_syntax(broken_code, error_msg))

    def generate_paper_code_response(
        self,
        query: str,
        context: str = "",
        paper_id: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Generates code for user requests related to paper implementation.
        Executes parallel Gemini + Hugging Face Qwen 2.5 Coder synthesis.
        Enforces AST syntax validation and cross-engine failover:
          - If primary candidate has syntax errors, auto-fails over to secondary.
          - If both have syntax errors, executes an automatic 1-turn repair prompt.
        """
        code_prompt = build_code_synthesis_user_prompt(query, context)
        candidates = self.generate_dual_candidates_sync(code_prompt, system_instruction=CODE_SYNTHESIS_SYSTEM_PROMPT)

        cand_hf = candidates.get("huggingface", {})
        cand_gemini = candidates.get("gemini", {})

        hf_code = cand_hf.get("code", "")
        gemini_code = cand_gemini.get("code", "")

        hf_valid, hf_err = validate_code_syntax(hf_code) if hf_code else (False, "No HF code")
        gemini_valid, gemini_err = validate_code_syntax(gemini_code) if gemini_code else (False, "No Gemini code")

        # 1. Primary preference: Hugging Face Qwen 2.5 Coder if valid
        if hf_valid and cand_hf.get("raw"):
            return cand_hf["raw"], "Hugging Face (Qwen 2.5 Coder 32B)"

        # 2. Seamless Failover: If HF has syntax errors, fail over to Gemini if Gemini is valid
        if gemini_valid and cand_gemini.get("raw"):
            if cand_hf.get("raw"):
                print(f"[DualCodeEngine] HF code syntax error ({hf_err}). Seamlessly failing over to Google Gemini...")
            return cand_gemini["raw"], "Google Gemini 3.6 Flash (Failover)"

        # 3. If HF was valid and Gemini wasn't
        if hf_valid and cand_hf.get("raw"):
            return cand_hf["raw"], "Hugging Face (Qwen 2.5 Coder 32B)"

        # 4. If both have syntax errors, attempt 1-turn auto-repair
        best_candidate = cand_hf if (hf_code and len(hf_code) > len(gemini_code)) else cand_gemini
        broken_code = best_candidate.get("code", "") or hf_code or gemini_code
        broken_err = hf_err if best_candidate == cand_hf else gemini_err

        if broken_code:
            print(f"[DualCodeEngine] Syntax errors detected ({broken_err}). Running 1-turn automatic repair...")
            repaired_code, repair_engine = self.repair_code_syntax_sync(broken_code, broken_err or "SyntaxError")
            if repaired_code:
                wrapped_repair = f"```python\n{repaired_code}\n```"
                return wrapped_repair, f"{repair_engine} (Auto-Repaired)"

        # 5. Fallback to best available raw output
        if cand_hf.get("raw"):
            return cand_hf["raw"], "Hugging Face (Qwen 2.5 Coder 32B)"
        elif cand_gemini.get("raw"):
            return cand_gemini["raw"], "Google Gemini 3.6 Flash"

        return "", ""


# Global singleton instance
dual_code_engine = DualCodeEngine()
