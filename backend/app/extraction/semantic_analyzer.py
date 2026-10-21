"""
Semantic Research Analyzer for Scientific Documents.

Separates high-level academic conceptual reasoning (Methodology, Contributions, Innovations,
Losses, Hyperparameters, Limitations) from low-level deterministic structural extraction.
"""

import os
import json
import requests
from typing import Dict, Any, Optional, List
from app.core.config import settings
from app.schemas.canonical_paper import PaperDocument


class SemanticResearchAnalyzer:
    """Extracts conceptual research themes and methodology summaries from a canonical PaperDocument."""

    def __init__(self):
        self.openrouter_key = settings.OPENROUTER_API_KEY
        self.gemini_key = settings.GEMINI_API_KEY

    def analyze_document_semantics(self, doc: PaperDocument) -> Dict[str, Any]:
        """
        Synthesizes research problem, core innovations, theoretical methodology,
        and experimental conclusions from canonical sections.
        """
        title = doc.metadata.title or "Scientific Paper"
        abstract = doc.metadata.abstract or ""
        
        # Collect key methodological sections
        methodology_text = ""
        results_text = ""
        for sec in doc.sections:
            sec_lower = sec.title.lower()
            if any(k in sec_lower for k in ["method", "architecture", "model", "approach", "framework", "formulation"]):
                methodology_text += f"\n### {sec.title}\n{sec.content[:2000]}"
            elif any(k in sec_lower for k in ["result", "experiment", "evaluation", "ablation", "benchmark"]):
                results_text += f"\n### {sec.title}\n{sec.content[:2000]}"

        # If abstract and methodology are empty, provide fallback
        if not abstract and not methodology_text:
            return self._build_fallback_semantics(title, abstract)

        # Dispatch prompt to synthesize structured conceptual summary
        prompt = (
            f"Analyze this research paper: '{title}'.\n\n"
            f"ABSTRACT:\n{abstract}\n\n"
            f"METHODOLOGY EXCERPTS:\n{methodology_text[:3500]}\n\n"
            f"RESULTS EXCERPTS:\n{results_text[:2000]}\n\n"
            "Synthesize a strict JSON object with this exact schema:\n"
            "{\n"
            '  "research_problem": "One-line definition of the core scientific bottleneck.",\n'
            '  "core_methodology": "Summary of the proposed architectural framework.",\n'
            '  "key_contributions": ["Contribution 1", "Contribution 2", "Contribution 3"],\n'
            '  "innovations": ["Novel mechanism 1", "Novel mechanism 2"],\n'
            '  "theoretical_foundation": "Key mathematical or theoretical equations used.",\n'
            '  "experimental_findings": "Summary of top benchmark results and datasets.",\n'
            '  "limitations": ["Identified limitation 1", "Identified limitation 2"]\n'
            "}"
        )

        try:
            raw_json = self._call_reasoning_llm(prompt)
            if raw_json and "{" in raw_json:
                clean = raw_json.strip()
                if "```json" in clean:
                    clean = clean.split("```json")[-1].split("```")[0].strip()
                elif "```" in clean:
                    clean = clean.split("```")[1].split("```")[0].strip()
                return json.loads(clean)
        except Exception as e:
            print(f"[SEMANTICS WARN] Semantic analysis LLM notice: {e}")

        return self._build_fallback_semantics(title, abstract)

    def _call_reasoning_llm(self, prompt: str) -> Optional[str]:
        """Calls OpenRouter or Gemini for conceptual synthesis."""
        if self.openrouter_key:
            try:
                resp = requests.post(
                    "https://openrouter.ai/api/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.openrouter_key}", "Content-Type": "application/json"},
                    json={
                        "model": "google/gemini-2.5-flash:free",
                        "messages": [{"role": "user", "content": prompt}],
                        "temperature": 0.2,
                        "max_tokens": 1024
                    },
                    timeout=15
                )
                if resp.status_code == 200:
                    return resp.json().get("choices", [{}])[0].get("message", {}).get("content")
            except Exception:
                pass

        if self.gemini_key:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={self.gemini_key}"
                resp = requests.post(
                    url,
                    json={"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.2}},
                    timeout=15
                )
                if resp.status_code == 200:
                    return resp.json().get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text")
            except Exception:
                pass

        return None

    def _build_fallback_semantics(self, title: str, abstract: str) -> Dict[str, Any]:
        """Provides clean heuristic fallback semantics without model execution."""
        return {
            "research_problem": f"Automated understanding and implementation of {title}.",
            "core_methodology": abstract[:300] if abstract else "Deep learning methodology extracted from document.",
            "key_contributions": ["Extracted architecture modules", "Reproducible parameter representations"],
            "innovations": ["Layout-aware neural parsing", "Multi-modal element transcription"],
            "theoretical_foundation": "Loss formulations and neural layer definitions.",
            "experimental_findings": "Extracted evaluation metric benchmarks.",
            "limitations": ["Document-specific layout constraints"]
        }
