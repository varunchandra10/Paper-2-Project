"""
Dedicated Vision-Language Model (VLM) Element Processor.

Executes surgical visual extraction on cropped image candidates (Figures, Tables, Equations)
using configurable multimodal providers (Google Gemini or OpenRouter) with strict structured JSON output.
"""

import os
import re
import json
import base64
import requests
from typing import Dict, Any, Optional, List
from app.core.config import settings
from app.core.quota_tracker import quota_tracker

# ─── Configurable Provider & Models ──────────────────────────────────────────────
DEFAULT_VLM_PROVIDER = getattr(settings, "VLM_PROVIDER", "google").lower()
DEFAULT_VLM_MODEL = getattr(settings, "VLM_MODEL", "gemini-2.0-flash")
OPENROUTER_VLM_MODEL = getattr(settings, "OPENROUTER_VLM_MODEL", "google/gemini-2.0-flash-exp:free")


def _encode_image_to_base64(image_path: str) -> Optional[str]:
    """Reads a local image file and returns base64 encoded string."""
    if not image_path or not os.path.exists(image_path):
        return None
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    except Exception as e:
        print(f"[VLM WARN] Could not encode image {image_path}: {e}")
        return None


def _clean_json_output(raw_text: str) -> str:
    """Strips Markdown fences to extract valid JSON payload."""
    if not raw_text:
        return "{}"
    text = raw_text.strip()
    if "```json" in text:
        text = text.split("```json")[-1].split("```")[0].strip()
    elif "```" in text:
        text = text.split("```")[1].split("```")[0].strip()
    return text


def _repair_json_latex(raw_text: str) -> dict:
    """Repairs unescaped LaTeX backslashes before JSON decoding."""
    cleaned = _clean_json_output(raw_text)
    try:
        return json.loads(cleaned)
    except Exception:
        pass
    # Escape lone backslashes (e.g. \alpha, \sum)
    fixed = re.sub(r'\\(?![/"\\bfnrtu])', r'\\\\', cleaned)
    try:
        return json.loads(fixed)
    except Exception:
        return {}


class VLMElementProcessor:
    """Processes visual element crops into structured semantic representations."""

    def __init__(
        self,
        provider: str = DEFAULT_VLM_PROVIDER,
        model: Optional[str] = None
    ):
        self.provider = provider
        self.model = model or (DEFAULT_VLM_MODEL if provider == "google" else OPENROUTER_VLM_MODEL)

    def process_figure(
        self,
        element_id: str,
        image_path: str,
        caption: str = ""
    ) -> Dict[str, Any]:
        """
        Interprets model architecture flowcharts, pipeline diagrams, and plots.
        Returns structured description, components list, and confidence score.
        """
        prompt = (
            f"Analyze this scientific paper diagram (Caption: '{caption}').\n"
            "Return a strictly valid JSON object with the following schema:\n"
            "{\n"
            f'  "element_id": "{element_id}",\n'
            '  "element_type": "figure",\n'
            '  "visual_description": "Detailed explanation of the flowchart or architecture showing dataflow and blocks.",\n'
            '  "components": ["List of key neural modules, layers, or components detected"],\n'
            '  "relationships": ["Directional connections or flow arrows (e.g. Encoder -> Attention -> Decoder)"],\n'
            '  "confidence": 0.95\n'
            "}"
        )

        res = self._call_vlm(image_path, prompt)
        parsed = _repair_json_latex(res.get("text", ""))

        return {
            "element_id": element_id,
            "element_type": "figure",
            "caption": caption,
            "visual_description": parsed.get("visual_description") or f"Figure illustrating {caption}",
            "components": parsed.get("components") or [],
            "relationships": parsed.get("relationships") or [],
            "image_path": image_path,
            "confidence": float(parsed.get("confidence", 0.90)),
            "tokens_used": res.get("tokens", 0)
        }

    def process_table(
        self,
        element_id: str,
        image_path: str,
        caption: str = "",
        fallback_text: str = ""
    ) -> Dict[str, Any]:
        """
        Transcribes tabular grids into clean Markdown tables with preserved numbers and uncertainty.
        """
        prompt = (
            f"Transcribe this table image into a clean Markdown table (Caption: '{caption}').\n"
            "Preserve all numerical precision, ± uncertainty values, and column headers.\n"
            "Return a strictly valid JSON object with schema:\n"
            "{\n"
            f'  "element_id": "{element_id}",\n'
            '  "element_type": "table",\n'
            '  "headers": ["Col 1", "Col 2", "Col 3"],\n'
            '  "rows": [["val1", "val2", "val3"]],\n'
            '  "content_markdown": "| Col 1 | Col 2 |\\n|---|---|\\n| a | b |",\n'
            '  "confidence": 0.98\n'
            "}"
        )

        res = self._call_vlm(image_path, prompt)
        parsed = _repair_json_latex(res.get("text", ""))

        md_content = parsed.get("content_markdown")
        if not md_content or "|" not in md_content:
            # Fallback: create basic markdown table from fallback text if VLM failed
            md_content = self._format_text_to_markdown_table(fallback_text, caption)

        return {
            "element_id": element_id,
            "element_type": "table",
            "caption": caption,
            "headers": parsed.get("headers") or [],
            "rows": parsed.get("rows") or [],
            "content_markdown": md_content,
            "confidence": float(parsed.get("confidence", 0.92)),
            "tokens_used": res.get("tokens", 0)
        }

    def process_equation(
        self,
        element_id: str,
        image_path: str,
        caption: str = "",
        raw_text: str = ""
    ) -> Dict[str, Any]:
        """
        Transcribes mathematical formula image into valid LaTeX representation.
        """
        prompt = (
            f"Transcribe this mathematical formula into standard LaTeX code (Identifier: '{caption}').\n"
            "Return a strictly valid JSON object with schema:\n"
            "{\n"
            f'  "element_id": "{element_id}",\n'
            '  "element_type": "equation",\n'
            '  "latex": "\\\\mathcal{L}_{total} = \\\\sum_{i=1}^N ...",\n'
            '  "variables": ["L", "N", "lambda"],\n'
            '  "confidence": 0.96\n'
            "}"
        )

        res = self._call_vlm(image_path, prompt)
        parsed = _repair_json_latex(res.get("text", ""))

        latex = parsed.get("latex") or raw_text.strip()
        return {
            "element_id": element_id,
            "element_type": "equation",
            "caption": caption,
            "latex": latex,
            "variables": parsed.get("variables") or [],
            "confidence": float(parsed.get("confidence", 0.90)),
            "tokens_used": res.get("tokens", 0)
        }

    def _call_vlm(self, image_path: str, prompt: str) -> Dict[str, Any]:
        """Dispatches multimodal vision request to Google Gemini or OpenRouter."""
        base64_img = _encode_image_to_base64(image_path)
        if not base64_img:
            return {"text": "{}", "tokens": 0}

        # 1. Google AI Studio Direct Pathway
        if self.provider == "google" and settings.GEMINI_API_KEY:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={settings.GEMINI_API_KEY}"
                payload = {
                    "contents": [{
                        "parts": [
                            {"text": prompt},
                            {"inline_data": {"mime_type": "image/png", "data": base64_img}}
                        ]
                    }],
                    "generationConfig": {"temperature": 0.1, "maxOutputTokens": 1024}
                }
                resp = requests.post(url, json=payload, timeout=12)
                if resp.status_code == 200:
                    d = resp.json()
                    candidates = d.get("candidates", [])
                    if candidates:
                        text = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                        tokens = d.get("usageMetadata", {}).get("totalTokenCount", 300)
                        return {"text": text, "tokens": tokens}
            except Exception as e:
                print(f"[VLM WARN] Google AI Studio VLM call error: {e}")

        # 2. OpenRouter Multimodal Pathway
        if settings.OPENROUTER_API_KEY:
            try:
                url = "https://openrouter.ai/api/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": self.model if "/" in self.model else "google/gemini-2.0-flash-exp:free",
                    "messages": [{
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_img}"}}
                        ]
                    }],
                    "temperature": 0.1,
                    "max_tokens": 1024
                }
                resp = requests.post(url, headers=headers, json=payload, timeout=14)
                if resp.status_code == 200:
                    d = resp.json()
                    choices = d.get("choices", [])
                    if choices:
                        text = choices[0].get("message", {}).get("content", "")
                        tokens = d.get("usage", {}).get("total_tokens", 350)
                        return {"text": text, "tokens": tokens}
            except Exception as e:
                print(f"[VLM WARN] OpenRouter VLM call error: {e}")

        return {"text": "{}", "tokens": 0}

    def _format_text_to_markdown_table(self, text: str, caption: str) -> str:
        """Deterministic fallback converting raw tabular text into basic Markdown table."""
        if not text:
            return f"| Table |\n|---|\n| {caption} |"
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        if not lines:
            return f"| Table |\n|---|\n| {caption} |"

        header_tokens = re.split(r'\s{2,}|\t', lines[0])
        col_count = max(2, len(header_tokens))
        md_lines = ["| " + " | ".join(header_tokens) + " |"]
        md_lines.append("| " + " | ".join(["---"] * col_count) + " |")

        for line in lines[1:]:
            row_tokens = re.split(r'\s{2,}|\t', line)
            while len(row_tokens) < col_count:
                row_tokens.append("-")
            md_lines.append("| " + " | ".join(row_tokens[:col_count]) + " |")

        return "\n".join(md_lines)
