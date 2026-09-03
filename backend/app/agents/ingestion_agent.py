"""
ingestion_agent.py
==================
Full-pipeline paper ingestion.

Flow
----
PDF Path
  ├── route_and_extract()     → raw assessment (inspector + PyMuPDF + GROBID + Docling)
  ├── _extract_title()        → 3-tier title (GROBID → Docling H1 → PyMuPDF font-size)
  ├── _extract_authors()      → GROBID structured author list
  ├── _extract_abstract()     → GROBID abstract paragraphs → PyMuPDF fallback
  ├── _build_sections()       → full section + sub-section tree
  ├── _extract_tables_as_md() → tables as Markdown strings
  ├── _extract_equations()    → GROBID formulas + inline LaTeX regex
  └── PaperDocument           → saved to EXTRACTED_JSON_DIR/{paper_id}.json
"""

import json
import os
import re
from typing import Any, Dict, List

from app.core.config import settings
from app.extraction.router import route_and_extract
from app.schemas.paper import PaperDocument, PaperMetadata, PaperSection


# ── Title quality guard ────────────────────────────────────────────────────────
_TITLE_REJECT = re.compile(
    r"""^\s*(
        vol(?:ume)?[\.\s]?\d | \d{4}\s*[-\u2013]\s*\d{4}
      | doi\s*: | http[s]?:// | copyright\s*\u00a9
      | ieee\b | elsevier\b | springer\b | mdpi\b
      | arxiv\s*:\s*\d | received\b | accepted\b | published\b
      | journal\s+of | proceedings\s+of | transactions\s+on
      | \d{1,2}\s+\w+\s+\d{4} | page\s+\d | manuscript\s+id
      | under\s+review | preprint | letters\s+on
      | international\s+journal
    )""",
    re.IGNORECASE | re.VERBOSE,
)
_TITLE_MIN, _TITLE_MAX = 15, 300


def _is_valid_title(text: str) -> bool:
    text = text.strip()
    if not (_TITLE_MIN <= len(text) <= _TITLE_MAX):
        return False
    if _TITLE_REJECT.match(text):
        return False
    alpha = sum(c.isalpha() for c in text) / max(len(text), 1)
    return alpha >= 0.40


def _clean_title(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"^\d+[\.\s]+", "", text).strip()
    return text


# ── Extraction helpers ─────────────────────────────────────────────────────────

def _extract_title(route_result: dict, docling_md: str) -> str:
    """3-tier title extraction: GROBID → Docling H1 → PyMuPDF font-size."""
    # Tier 1: GROBID structured XML title
    g = (route_result.get("grobid_output") or {}).get("title", "")
    t = _clean_title(g)
    if _is_valid_title(t):
        return t

    # Tier 2: First heading in Docling Markdown
    for line in (docling_md or "").splitlines():
        if line.strip().startswith("#"):
            candidate = _clean_title(re.sub(r"^#+\s*", "", line.strip()))
            if _is_valid_title(candidate):
                return candidate

    # Tier 3: PyMuPDF largest-font block on page 1
    t = _clean_title((route_result.get("pymupdf_output") or {}).get("title", ""))
    if _is_valid_title(t):
        return t

    return "Unknown Title"


def _extract_authors(route_result: dict) -> List[str]:
    return [a for a in (route_result.get("grobid_output") or {}).get("authors", []) if a]


def _extract_abstract(route_result: dict) -> str:
    abstract = ((route_result.get("grobid_output") or {}).get("abstract") or "").strip()
    if abstract:
        return abstract
    # PyMuPDF fallback
    for key, sec in ((route_result.get("pymupdf_output") or {}).get("sections") or {}).items():
        if "abstract" in key.lower():
            return (sec.get("content") or "").strip()
    return ""


def _build_sections(route_result: dict) -> List[PaperSection]:
    """Full section + sub-section tree. PyMuPDF primary, GROBID fallback."""
    sections: List[PaperSection] = []

    # Primary: PyMuPDF detect_sections (numbered headings + nested subsections)
    py_secs = (route_result.get("pymupdf_output") or {}).get("sections") or {}
    for sec_name, sec_data in py_secs.items():
        if sec_name.lower() in ("tables", "metadata / front matter"):
            continue
        content = (sec_data.get("content") or "").strip()
        full_content = content
        for sub_name, sub_text in (sec_data.get("subsections") or {}).items():
            sub_text = (sub_text or "").strip()
            if sub_text:
                full_content += f"\n\n### {sub_name}\n{sub_text}"
        if full_content.strip():
            sections.append(PaperSection(title=sec_name, content=full_content.strip()))

    # Fallback: GROBID body divs
    if not sections:
        gr_secs = (route_result.get("grobid_output") or {}).get("sections") or {}
        for sec_name, sec_data in gr_secs.items():
            content = (sec_data.get("content") or "").strip()
            full_content = content
            for sub_name, sub_text in (sec_data.get("subsections") or {}).items():
                if sub_text:
                    full_content += f"\n\n### {sub_name}\n{sub_text.strip()}"
            if full_content.strip():
                sections.append(PaperSection(title=sec_name, content=full_content.strip()))

    return sections


def _extract_tables_as_md(route_result: dict) -> List[Dict[str, Any]]:
    """Collects tables from Docling (best), GROBID, and PyMuPDF."""
    tables, seen, idx = [], set(), 1

    def _add(caption: str, md: str, source: str):
        nonlocal idx
        key = caption.strip().lower()[:60]
        if key not in seen and md and md.strip():
            seen.add(key)
            tables.append({"table_num": idx, "caption": caption,
                           "content_markdown": md.strip(), "source": source})
            idx += 1

    for t in (route_result.get("docling_output") or {}).get("tables", []):
        _add(str(t.get("caption") or f"Table {idx}"),
             t.get("content_markdown") or t.get("content") or "", "docling")

    for t in (route_result.get("grobid_output") or {}).get("tables", []):
        raw = t.get("content") or ""
        if raw:
            _add(str(t.get("caption") or f"Table {idx}"),
                 f"```\n{raw}\n```", "grobid")

    for sec_data in ((route_result.get("pymupdf_output") or {}).get("sections") or {}).values():
        for sub_name, sub_md in (sec_data.get("subsections") or {}).items():
            if "table" in sub_name.lower():
                _add(sub_name, sub_md, "pymupdf")

    return tables


def _extract_equations(route_result: dict, full_text: str) -> List[Dict[str, str]]:
    """GROBID formula elements + inline LaTeX regex fallback."""
    equations, seen = [], set()

    for eq in (route_result.get("grobid_output") or {}).get("equations", []):
        latex = (eq.get("latex") or "").strip()
        if latex and latex not in seen:
            seen.add(latex)
            equations.append({"caption": eq.get("caption", "Equation"),
                               "latex": latex, "source": "grobid"})

    if full_text:
        for m in re.finditer(r"\$\$(.+?)\$\$", full_text, re.DOTALL):
            latex = m.group(1).strip()
            if latex and latex not in seen and len(latex) < 500:
                seen.add(latex)
                equations.append({"caption": "Display Equation",
                                   "latex": f"$${latex}$$", "source": "regex"})
        for m in re.finditer(r"(?<!\$)\$(?!\$)(.{3,120}?)(?<!\$)\$(?!\$)", full_text):
            latex = m.group(1).strip()
            if latex and latex not in seen:
                seen.add(latex)
                equations.append({"caption": "Inline Equation",
                                   "latex": f"${latex}$", "source": "regex"})

    return equations


def _assemble_raw_text(route_result: dict) -> str:
    parts: List[str] = []
    grobid = route_result.get("grobid_output") or {}
    if grobid.get("abstract"):
        parts.append(grobid["abstract"])
    for sec_name, sec_data in (grobid.get("sections") or {}).items():
        parts.append(f"\n\n{sec_name}\n{sec_data.get('content', '')}")
    docling = route_result.get("docling_output") or {}
    if docling.get("markdown"):
        parts.append(docling["markdown"])
    pymupdf = route_result.get("pymupdf_output") or {}
    for sec_name, sec_data in (pymupdf.get("sections") or {}).items():
        if sec_name.lower() not in ("tables",):
            parts.append(sec_data.get("content", ""))
            for sub_text in (sec_data.get("subsections") or {}).values():
                parts.append(sub_text or "")
    return "\n\n".join(p for p in parts if p and p.strip())


# ── Public API ─────────────────────────────────────────────────────────────────

def run_ingestion_agent(pdf_path: str, model_name: str = settings.DEFAULT_MODEL) -> PaperDocument:
    """
    Full-pipeline ingestion of a single research paper PDF.

    Parameters
    ----------
    pdf_path   : absolute path to the PDF
    model_name : Ollama model (reserved; extraction is rule-based)

    Returns
    -------
    PaperDocument with title, authors, abstract, sections (with subsections),
    tables (as Markdown), equations, figures. Also saves canonical JSON.
    """
    print(f"  [INGESTION] {os.path.basename(pdf_path)}")
    route_result = route_and_extract(pdf_path)
    parsers = route_result.get("selected_parsers", [])
    print(f"  [INGESTION] Parsers: {parsers}")

    docling_md = (route_result.get("docling_output") or {}).get("markdown", "")
    raw_text   = _assemble_raw_text(route_result)

    title    = _extract_title(route_result, docling_md)
    authors  = _extract_authors(route_result)
    abstract = _extract_abstract(route_result)
    sections = _build_sections(route_result)
    tables   = _extract_tables_as_md(route_result)
    equations = _extract_equations(route_result, raw_text)
    figures  = (route_result.get("grobid_output") or {}).get("figures", [])

    print(f"  [INGESTION] title='{title[:60]}' sections={len(sections)} tables={len(tables)} eqs={len(equations)}")

    # Domain inference from section headings
    hints = " ".join(s.title for s in sections[:6]).lower()
    domain = "Machine Learning / Computer Vision"
    for kws, label in [
        (["remote sensing"],           "Remote Sensing / Computer Vision"),
        (["change detection"],         "Remote Sensing / Change Detection"),
        (["medical", "clinical"],      "Medical Image Analysis"),
        (["natural language", "nlp"],  "Natural Language Processing"),
        (["graph neural"],             "Graph Neural Networks"),
        (["reinforcement"],            "Reinforcement Learning"),
        (["segmentation"],             "Semantic Segmentation"),
        (["object detection"],         "Object Detection"),
        (["time series"],              "Time-Series Analysis"),
    ]:
        if any(k in hints for k in kws):
            domain = label
            break

    paper_id = route_result.get("paper_id",
                os.path.splitext(os.path.basename(pdf_path))[0])

    metadata = PaperMetadata(
        title=title, authors=authors, abstract=abstract, domain=domain,
    )
    doc = PaperDocument(
        paper_id=paper_id, metadata=metadata,
        sections=sections, tables=tables, figures=figures,
        raw_full_text=raw_text[:50_000],
    )

    # Persist canonical JSON
    os.makedirs(settings.EXTRACTED_JSON_DIR, exist_ok=True)
    out_path = os.path.join(settings.EXTRACTED_JSON_DIR, f"{paper_id}.json")
    canonical = {
        "paper_id": paper_id,
        "metadata": metadata.model_dump(),
        "sections": [
            {"title": s.title, "content": s.content,
             "section_num": s.section_num, "page": s.page}
            for s in sections
        ],
        "tables": tables,
        "figures": figures,
        "equations": equations,
        "raw_full_text_chars": len(raw_text),
        "parsers_used": parsers,
    }
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(canonical, fh, indent=2, ensure_ascii=False, default=str)
    print(f"  [INGESTION] Saved -> {out_path}")

    return doc
