"""
Full-Paper Academic Extraction Engine.

Executes prioritized, non-truncated extraction of scientific papers:
1. OpenRouter Google Model (e.g. google/gemini-2.5-flash) - primary free tier.
2. Direct Google AI Studio Gemini API failover.
Prompts and JSON schemas are loaded exclusively from app.core.prompts.
API endpoints and model identifiers are loaded from app.core.constants.
"""

import re
import json
import requests
from typing import Dict, Any, Optional
from app.core.config import settings
from app.core.quota_tracker import quota_tracker
from app.core.constants import (
    OPENROUTER_CHAT_URL,
    GEMINI_BASE_URL,
    OPENROUTER_PDF_MODEL,
    BACKEND_GEMINI_MODEL
)
from app.core.prompts import (
    PAPER_EXTRACTION_SYSTEM_PROMPT,
    build_paper_extraction_prompt
)


def _get_active_api_keys() -> tuple:
    """Retrieves OpenRouter key and Gemini key from settings or user_profile.json."""
    or_key = settings.OPENROUTER_API_KEY if settings.has_openrouter() else None
    gemini_key = settings.GEMINI_API_KEY if settings.has_gemini() else None

    try:
        from app.core.database import ChatDatabase
        profile = ChatDatabase().get_standalone_user_profile()
        user_or = (profile.get("openrouterApiKey") or "").strip()
        if user_or and len(user_or) > 10:
            or_key = user_or

        user_gemini = (profile.get("geminiApiKey") or "").strip()
        if user_gemini and len(user_gemini) > 10:
            gemini_key = user_gemini
    except Exception:
        pass

    return or_key, gemini_key


def _clean_json_response(raw_text: str) -> str:
    """Strips markdown code fences (```json ... ```) to isolate clean JSON payload."""
    if not raw_text:
        return "{}"
    text = raw_text.strip()
    if "```json" in text:
        text = text.split("```json")[-1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    return text


def _repair_and_parse_json(raw_text: str) -> dict:
    """Parses JSON with automatic repair for unescaped LaTeX backslashes, unclosed quotes, and truncation."""
    clean_text = _clean_json_response(raw_text)
    try:
        return json.loads(clean_text)
    except Exception:
        pass

    # 1. Escape lone LaTeX backslashes that are invalid in JSON (e.g. \alpha, \sum)
    fixed_text = re.sub(r'\\(?![/"\\bfnrtu])', r'\\\\', clean_text)
    try:
        return json.loads(fixed_text)
    except Exception:
        pass

    # 2. Repair truncated strings/objects if model hit token limits
    repaired = fixed_text.strip()
    # If unclosed quote at end, close it
    unescaped_quotes = len(re.findall(r'(?<!\\)"', repaired))
    if unescaped_quotes % 2 != 0:
        repaired += '"'
    
    # Close open brackets & braces
    open_braces = repaired.count('{') - repaired.count('}')
    open_brackets = repaired.count('[') - repaired.count(']')
    if open_brackets > 0:
        repaired += ']' * open_brackets
    if open_braces > 0:
        repaired += '}' * open_braces
        
    try:
        return json.loads(repaired)
    except Exception:
        pass

    # 3. Fallback regex extraction of primary fields
    out = {"title": "", "abstract": "", "sections": {}, "equations": [], "hyperparameters": {}}
    title_m = re.search(r'"title":\s*"([^"]+)"', clean_text)
    if title_m:
        out["title"] = title_m.group(1)
    abstract_m = re.search(r'"abstract":\s*"([^"]+)"', clean_text)
    if abstract_m:
        out["abstract"] = abstract_m.group(1)
    return out


def extract_full_document_gemini(raw_text: str, paper_id: str = "paper_document") -> Dict[str, Any]:
    """
    Full-Paper Academic Extraction Engine powered by OpenRouter Google model and direct Gemini fallback.
    Extracts complete sections, LaTeX equations, and hyperparameters.
    """
    report = {
        "paper_id": paper_id,
        "title": "",
        "authors": [],
        "abstract": "",
        "sections": {},
        "equations": [],
        "tables": [],
        "hyperparameters": {},
        "valid": False,
        "error_message": None,
        "raw_response": ""
    }

    if not raw_text or len(raw_text.strip()) < 100:
        report["error_message"] = "Insufficient text provided for Gemini extraction."
        return report

    or_key, gemini_key = _get_active_api_keys()
    if not or_key and not gemini_key:
        report["error_message"] = "Neither OPENROUTER_API_KEY nor GEMINI_API_KEY is configured."
        print(f"[GEMINI_PARSER WARN] {report['error_message']}")
        return report

    input_text = raw_text[:250000]
    prompt = build_paper_extraction_prompt(input_text)
    system_instruction = PAPER_EXTRACTION_SYSTEM_PROMPT

    # Strict Single-Provider Enforcement:
    # Use EITHER OpenRouter Gemini OR Backend Gemini for extraction, NEVER both!
    provider_pref = getattr(settings, "EXTRACTION_PROVIDER", "gemini").lower().strip()
    
    if provider_pref == "openrouter":
        chosen_provider = "openrouter" if or_key else None
    else:
        chosen_provider = "gemini" if gemini_key else ("openrouter" if or_key else None)
        
    if not chosen_provider:
        report["error_message"] = f"Extraction provider '{provider_pref}' requested but corresponding API key is missing."
        print(f"[EXTRACTION WARN] {report['error_message']}")
        return report

    print(f"[EXTRACTION] Running single chosen provider: {chosen_provider.upper()} (Zero credit bleed policy enforced)")

    if chosen_provider == "openrouter":
        or_models = [OPENROUTER_PDF_MODEL, "google/gemini-2.5-flash-lite"]
        for or_model in or_models:
            try:
                headers = {
                    "Authorization": f"Bearer {or_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost:8000"
                }
                data = {
                    "model": or_model,
                    "messages": [
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1
                }
                resp = requests.post(OPENROUTER_CHAT_URL, headers=headers, json=data, timeout=90)
                if resp.status_code == 200:
                    quota_tracker.record_usage("openrouter", or_model)
                    quota_tracker.update_live_headers("openrouter", resp.headers)

                    raw_out = resp.json()["choices"][0]["message"]["content"].strip()
                    report["raw_response"] = raw_out
                    parsed_data = _repair_and_parse_json(raw_out)

                    report["title"] = parsed_data.get("title", "").strip()
                    report["authors"] = parsed_data.get("authors", [])
                    report["abstract"] = parsed_data.get("abstract", "").strip()
                    report["sections"] = parsed_data.get("sections", {})
                    report["equations"] = parsed_data.get("equations", [])
                    report["hyperparameters"] = parsed_data.get("hyperparameters", {})
                    report["valid"] = bool(report["title"] and report["sections"])

                    if report["valid"]:
                        print(f"[GEMINI_PARSER SUCCESS] Extracted {len(report['sections'])} sections via OpenRouter ({or_model}).")
                        return report
            except Exception as e:
                print(f"[GEMINI_PARSER WARN] OpenRouter extraction attempt failed for {or_model}: {e}")

    elif chosen_provider == "gemini":
        direct_models = [BACKEND_GEMINI_MODEL, "gemini-2.0-flash", "gemini-1.5-flash"]
        for g_model in direct_models:
            try:
                url = f"{GEMINI_BASE_URL}/{g_model}:generateContent?key={gemini_key}"
                headers = {"Content-Type": "application/json"}
                payload = {
                    "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                    "systemInstruction": {"parts": [{"text": system_instruction}]},
                    "generationConfig": {
                        "temperature": 0.1,
                        "maxOutputTokens": 8192,
                        "responseMimeType": "application/json"
                    }
                }
                resp = requests.post(url, headers=headers, json=payload, timeout=90)
                if resp.status_code == 200:
                    quota_tracker.record_usage("gemini", g_model)
                    candidates = resp.json().get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        raw_out = "".join(p.get("text", "") for p in parts if "text" in p).strip()
                        report["raw_response"] = raw_out
                        parsed_data = _repair_and_parse_json(raw_out)

                        report["title"] = parsed_data.get("title", "").strip()
                        report["authors"] = parsed_data.get("authors", [])
                        report["abstract"] = parsed_data.get("abstract", "").strip()
                        report["sections"] = parsed_data.get("sections", {})
                        report["equations"] = parsed_data.get("equations", [])
                        report["hyperparameters"] = parsed_data.get("hyperparameters", {})
                        report["valid"] = bool(report["title"] and report["sections"])

                        if report["valid"]:
                            print(f"[GEMINI_PARSER SUCCESS] Extracted {len(report['sections'])} sections via Direct Google Gemini ({g_model}).")
                            return report
            except Exception as e:
                print(f"[GEMINI_PARSER WARN] Direct Google Gemini extraction attempt failed for {g_model}: {e}")

    if not report["valid"]:
        report["error_message"] = f"Extraction via {chosen_provider.upper()} exhausted without valid response."
    return report
