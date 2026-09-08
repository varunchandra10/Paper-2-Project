import re
from typing import Optional, Any
from app.core.config import settings


def generate_smart_title(
    query: str,
    paper_id: Optional[str] = None,
    answer_snippet: Optional[str] = None,
    current_title: Optional[str] = None,
    db: Optional[Any] = None,
    model_router: Optional[Any] = None
) -> str:
    """Generates a concise, punchy 3-5 word conversation title like ChatGPT/Claude/Gemini."""
    resolved_paper_title = None
    if db and paper_id:
        try:
            resolved_paper_title = db.get_paper_title_by_id_or_name(paper_id, None)
        except Exception:
            pass

    # Fast LLM Title Prompt
    titling_prompt = (
        "You are an AI conversation title generator like ChatGPT and Claude.\n"
        "Generate a concise, punchy conversation title (3 to 5 words maximum, under 32 characters) summarizing the user's inquiry.\n\n"
        f"Context: {resolved_paper_title or paper_id or 'Research'}\n"
        f"User Prompt: {query}\n"
        f"Assistant Answer Snippet: {(answer_snippet or '')[:180]}\n\n"
        "Rules:\n"
        "1. Output MUST be 3 to 5 words (maximum 32 characters).\n"
        "2. Title Case, noun-phrase style (e.g. 'E-SGCD Deep Dive', 'CASGF Module Breakdown', 'LEVIR-CD Benchmark Audit').\n"
        "3. Do NOT use quotes, colons, brackets, or trailing punctuation.\n"
        "4. Never output filler like 'Chat with AI', 'New Conversation', 'Question Regarding', or 'Analysis of'.\n"
        "5. Output ONLY the raw title text.\n\n"
        "Title:"
    )

    try:
        # Preserve Groq's 8,000 TPM limit exclusively for user chat responses.
        # Titling uses high-capacity OpenRouter or Gemini, falling back to heuristic instantly.
        raw_title = ""
        if settings.OPENROUTER_API_KEY and model_router:
            from app.core.constants import OPENROUTER_PDF_MODEL
            raw_title, _ = model_router.generate(titling_prompt, model_id=OPENROUTER_PDF_MODEL)
        elif settings.has_gemini():
            import httpx
            # API key in header only — never in URL
            g_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
            g_headers = {"Content-Type": "application/json", "x-goog-api-key": settings.GEMINI_API_KEY}
            g_payload = {
                "contents": [{"role": "user", "parts": [{"text": titling_prompt}]}],
                "generationConfig": {"temperature": 0.2, "maxOutputTokens": 64}
            }
            g_resp = httpx.post(g_url, headers=g_headers, json=g_payload, timeout=10.0)
            if g_resp.status_code == 200:
                candidates = g_resp.json().get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    raw_title = parts[0].get("text", "") if parts else ""

        clean_title = raw_title.strip().strip('"\'`').replace("\n", " ")
        clean_title = re.sub(r'^(Title:\s*|Conversation:\s*)', '', clean_title, flags=re.IGNORECASE).strip()
        clean_title = clean_title.rstrip(".:;,-")
        if "⚠️" in clean_title or "rate limit" in clean_title.lower() or "error" in clean_title.lower():
            raise ValueError("Model returned warning message instead of title")
        words = clean_title.split()
        if len(words) > 5:
            clean_title = " ".join(words[:5])
        if clean_title and 3 <= len(clean_title) <= 40:
            return clean_title
    except Exception as e:
        print(f"[TITLER WARN] AI title generation fallback triggered ({e}).")

    # Heuristic fallback:
    prefix = "Paper"
    if resolved_paper_title:
        short_match = re.match(r'^([A-Za-z0-9\-]+)', resolved_paper_title)
        if short_match:
            prefix = short_match.group(1)
    elif paper_id:
        clean_pid = paper_id.replace("paper_", "").replace("_", " ").title()
        words_p = clean_pid.split()
        prefix = words_p[0] if words_p else "Paper"

    q_lower = query.lower()
    if any(w in q_lower for w in ["code", "implement", "pytorch"]):
        return f"{prefix} Code Implementation"
    if any(w in q_lower for w in ["explain", "overview", "what is", "about"]):
        return f"{prefix} Deep Dive"
    if any(w in q_lower for w in ["table", "metric", "result", "accuracy", "f1"]):
        return f"{prefix} Benchmark Audit"
    if any(w in q_lower for w in ["loss", "equation", "formula", "math"]):
        return f"{prefix} Formulation Details"

    words = query.strip().split()
    return " ".join(words[:4]).title() if words else f"{prefix} Analysis"
