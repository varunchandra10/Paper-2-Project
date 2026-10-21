import os
import re
from typing import List, Dict, Any, Optional
from app.schemas.canonical_paper import (
    PaperDocument,
    ExtractionQualityReport,
    ValidationMetric
)


def _roman_to_int(roman: str) -> int:
    """Helper to convert a Roman numeral string to an integer value."""
    roman_map = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    val = 0
    prev = 0
    for char in reversed(roman.upper()):
        curr = roman_map.get(char, 0)
        if curr < prev:
            val -= curr
        else:
            val += curr
        prev = curr
    return val


def validate_paper_document(doc: PaperDocument) -> ExtractionQualityReport:
    """
    Performs deterministic and element-level validation checks on a canonical PaperDocument.
    Evaluates factual preservation, bracket balance, table grid structure, numeric preservation,
    and returns ExtractionQualityReport with transparent assertions.
    """
    scorecard = {}
    conflicts_logged = []
    element_confidence: Dict[str, Any] = {
        "text": {"confidence": 1.0, "status": "validated", "checks": {}},
        "tables": {},
        "figures": {},
        "equations": {},
        "citations": {"confidence": 1.0, "status": "validated", "checks": {}}
    }

    total_points = 0
    max_points = 100

    # ── 1. Title Validation (15 pts) ──
    title = doc.metadata.title.strip() if doc.metadata.title else ""
    if not title or title.lower() in ("unknown title", "untitled"):
        scorecard["title_check"] = ValidationMetric(
            status="ERROR",
            message="Title is missing or unextracted.",
            details=f"Extracted title: '{title}'"
        )
    else:
        scorecard["title_check"] = ValidationMetric(
            status="SUCCESS",
            message="Title successfully extracted.",
            details=f"Title: '{title}'"
        )
        total_points += 15

    # ── 2. Abstract Validation (15 pts) ──
    abstract = doc.metadata.abstract.strip() if doc.metadata.abstract else ""
    if not abstract:
        scorecard["abstract_check"] = ValidationMetric(
            status="WARNING",
            message="Abstract is missing.",
            details=None
        )
    elif len(abstract) < 80:
        scorecard["abstract_check"] = ValidationMetric(
            status="WARNING",
            message="Abstract is abnormally short.",
            details=f"Abstract length: {len(abstract)} characters."
        )
        total_points += 8
    else:
        scorecard["abstract_check"] = ValidationMetric(
            status="SUCCESS",
            message="Abstract successfully extracted.",
            details=f"Abstract length: {len(abstract)} characters."
        )
        total_points += 15

    # ── 3. Section Ordering & Text Completeness (25 pts) ──
    sections = doc.sections
    text_checks = {
        "section_count_sufficient": len(sections) >= 2,
        "content_length_valid": sum(len(s.content) for s in sections) > 200,
        "sequence_ordered": True
    }

    if len(sections) < 2:
        scorecard["section_ordering"] = ValidationMetric(
            status="WARNING",
            message="Abnormally low section count.",
            details=f"Only {len(sections)} sections extracted."
        )
        total_points += 10
        text_checks["section_count_sufficient"] = False
    else:
        out_of_order = []
        idx_seq = []
        for sec in sections:
            m = re.match(r'^\s*(?:([IVXLCDM]+)|(\d+))\b', sec.title, re.IGNORECASE)
            if m:
                roman, arabic = m.groups()
                if arabic:
                    idx_seq.append((sec.title, int(arabic)))
                elif roman:
                    idx_seq.append((sec.title, _roman_to_int(roman)))

        for i in range(len(idx_seq) - 1):
            t1, v1 = idx_seq[i]
            t2, v2 = idx_seq[i + 1]
            if v2 <= v1:
                out_of_order.append(f"'{t2}' (val: {v2}) parsed after '{t1}' (val: {v1})")

        if out_of_order:
            scorecard["section_ordering"] = ValidationMetric(
                status="WARNING",
                message="Section headings are out of numerical order.",
                details=" | ".join(out_of_order)
            )
            total_points += 18
            text_checks["sequence_ordered"] = False
        else:
            scorecard["section_ordering"] = ValidationMetric(
                status="SUCCESS",
                message="Section headings are ordered logically.",
                details=f"Verified {len(sections)} sections in sequence."
            )
            total_points += 25

    passed_text_checks = sum(1 for v in text_checks.values() if v)
    text_conf = round(passed_text_checks / max(1, len(text_checks)), 2)
    element_confidence["text"] = {
        "confidence": text_conf,
        "status": "validated" if text_conf >= 0.8 else "warning",
        "checks": text_checks
    }

    # ── 4. Table Structure & Preservation Audit (15 pts) ──
    tables = doc.tables
    if not tables:
        scorecard["tables_check"] = ValidationMetric(
            status="SUCCESS",
            message="No tables detected in document.",
            details=None
        )
        total_points += 15
    else:
        invalid_tables = []
        for tab in tables:
            md = tab.content_markdown or ""
            has_pipes = "|" in md
            has_headers = "---" in md or len(tab.headers) > 0
            has_rows = len(tab.rows) > 0 or len([l for l in md.split("\n") if "|" in l]) >= 2
            has_caption = bool(tab.caption and len(tab.caption.strip()) > 3)
            # Numeric & uncertainty preservation check
            has_numeric = bool(re.search(r'\d', md))
            preserves_uncertainty = ("±" in md) or ("%" in md) or ("." in md) or not has_numeric

            checks = {
                "bbox_valid": tab.page >= 1,
                "caption_found": has_caption,
                "markdown_grid_valid": has_pipes and has_headers,
                "rows_present": has_rows,
                "numeric_preservation": preserves_uncertainty
            }

            passed = sum(1 for v in checks.values() if v)
            conf = round(passed / len(checks), 2)
            status = "validated" if conf >= 0.8 else "warning"

            if not (has_pipes and (has_headers or has_rows)):
                invalid_tables.append(tab.id)

            element_confidence["tables"][tab.id] = {
                "confidence": conf,
                "status": status,
                "checks": checks
            }

        if invalid_tables:
            scorecard["tables_check"] = ValidationMetric(
                status="WARNING",
                message="Some tables have irregular formatting.",
                details=f"Tables needing review: {', '.join(invalid_tables)}"
            )
            total_points += 10
        else:
            scorecard["tables_check"] = ValidationMetric(
                status="SUCCESS",
                message=f"All {len(tables)} tables verified with structured formatting.",
                details=f"Verified tables: {', '.join([t.id for t in tables])}"
            )
            total_points += 15

    # ── 5. Equations & LaTeX Syntax Audit (15 pts) ──
    equations = doc.equations
    if not equations:
        scorecard["equations_check"] = ValidationMetric(
            status="SUCCESS",
            message="No display equations detected.",
            details=None
        )
        total_points += 15
    else:
        invalid_equations = []
        for eq in equations:
            latex = eq.latex or ""
            open_b = latex.count("{")
            close_b = latex.count("}")
            open_p = latex.count("(")
            close_p = latex.count(")")
            open_sq = latex.count("[")
            close_sq = latex.count("]")

            checks = {
                "bbox_valid": eq.page >= 1,
                "latex_non_empty": len(latex.strip()) >= 2,
                "brace_balance": open_b == close_b,
                "parenthesis_balance": open_p == close_p,
                "bracket_balance": open_sq == close_sq,
                "math_syntax_valid": bool(re.search(r'[=+\-*/\\^_{}()_0-9a-zA-Z]', latex))
            }

            passed = sum(1 for v in checks.values() if v)
            conf = round(passed / len(checks), 2)
            status = "validated" if conf >= 0.8 else "warning"

            if not checks["brace_balance"] or not checks["latex_non_empty"]:
                invalid_equations.append(eq.id)

            element_confidence["equations"][eq.id] = {
                "confidence": conf,
                "status": status,
                "checks": checks
            }

        if invalid_equations:
            scorecard["equations_check"] = ValidationMetric(
                status="WARNING",
                message="Some equations contain unmatched braces or short fragments.",
                details=f"Equations: {', '.join(invalid_equations)}"
            )
            total_points += 10
        else:
            scorecard["equations_check"] = ValidationMetric(
                status="SUCCESS",
                message=f"All {len(equations)} mathematical equations validated.",
                details=f"Verified equations: {', '.join([e.id for e in equations])}"
            )
            total_points += 15

    # ── 6. Figures & Visual Description Audit (15 pts) ──
    figures = doc.figures
    if not figures:
        scorecard["figures_check"] = ValidationMetric(
            status="SUCCESS",
            message="No figures detected in document.",
            details=None
        )
        total_points += 15
    else:
        for fig in figures:
            has_caption = bool(fig.caption and len(fig.caption.strip()) > 3)
            image_exists = bool(fig.image_path and os.path.exists(fig.image_path))
            has_desc = bool(fig.visual_description and len(fig.visual_description.strip()) > 10)

            checks = {
                "bbox_valid": fig.page >= 1,
                "caption_found": has_caption,
                "image_file_exists": image_exists,
                "provenance_tracked": bool(fig.source)
            }
            if fig.source and fig.source.get("extraction_method") == "gemini_vlm":
                checks["visual_interpretation_present"] = has_desc

            passed = sum(1 for v in checks.values() if v)
            conf = round(passed / len(checks), 2)
            element_confidence["figures"][fig.id] = {
                "confidence": conf,
                "status": "validated" if conf >= 0.75 else "warning",
                "checks": checks
            }

        scorecard["figures_check"] = ValidationMetric(
            status="SUCCESS",
            message=f"Preserved {len(figures)} figures with provenance tracking.",
            details=f"Figures: {', '.join([f.id for f in figures])}"
        )
        total_points += 15

    # Compute overall completeness score
    completeness_score = round((total_points / max_points) * 100.0, 1)
    is_valid = not any(m.status == "ERROR" for m in scorecard.values())

    return ExtractionQualityReport(
        paper_id=doc.paper_id,
        valid=is_valid,
        completeness_score=completeness_score,
        element_confidence=element_confidence,
        scorecard=scorecard,
        conflicts_logged=conflicts_logged
    )

