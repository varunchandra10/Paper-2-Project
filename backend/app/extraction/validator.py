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
    Performs deterministic validation checks on a canonical PaperDocument.
    Generates an ExtractionQualityReport containing a validation scorecard.
    """
    scorecard = {}
    conflicts_logged = []

    # 1. Title Validation
    title = doc.metadata.title.strip() if doc.metadata.title else ""
    if not title or title.lower() in ("unknown title", "unknown", "untitled"):
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

    # 2. Abstract Validation
    abstract = doc.metadata.abstract.strip() if doc.metadata.abstract else ""
    if not abstract:
        scorecard["abstract_check"] = ValidationMetric(
            status="WARNING",
            message="Abstract is missing.",
            details=None
        )
    elif len(abstract) < 100:
        scorecard["abstract_check"] = ValidationMetric(
            status="WARNING",
            message="Abstract is abnormally short.",
            details=f"Abstract length: {len(abstract)} characters."
        )
    else:
        scorecard["abstract_check"] = ValidationMetric(
            status="SUCCESS",
            message="Abstract successfully extracted.",
            details=f"Abstract length: {len(abstract)} characters."
        )

    # 3. Section Ordering Check
    sections = doc.sections
    if len(sections) < 3:
        scorecard["section_ordering"] = ValidationMetric(
            status="WARNING",
            message="Abnormally low section count.",
            details=f"Only {len(sections)} sections extracted."
        )
    else:
        idx_seq = []
        for sec in sections:
            m = re.match(r'^\s*(?:([IVXLCDM]+)|(\d+))\b', sec.title, re.IGNORECASE)
            if m:
                roman, arabic = m.groups()
                if arabic:
                    idx_seq.append((sec.title, int(arabic)))
                elif roman:
                    val = _roman_to_int(roman)
                    idx_seq.append((sec.title, val))
                    
        out_of_order = []
        for i in range(len(idx_seq) - 1):
            t1, v1 = idx_seq[i]
            t2, v2 = idx_seq[i+1]
            if v2 <= v1:
                out_of_order.append(f"'{t2}' (val: {v2}) parsed after '{t1}' (val: {v1})")
                
        if out_of_order:
            scorecard["section_ordering"] = ValidationMetric(
                status="WARNING",
                message="Section headings are out of numerical order.",
                details=" | ".join(out_of_order)
            )
        else:
            scorecard["section_ordering"] = ValidationMetric(
                status="SUCCESS",
                message="Sections are in sequential order.",
                details=f"Verified {len(idx_seq)} numbered sections."
            )

    # 4. Text Duplication Check
    duplicated_sentences = []
    seen_sentences = {}
    
    for sec in sections:
        subs = getattr(sec, "subsections", {})
        sub_text = " ".join(subs.values()) if isinstance(subs, dict) else ""
        text = (getattr(sec, "content", "") or "") + " " + sub_text
        sentences = [s.strip() for s in re.split(r'\.\s+', text) if len(s.strip()) > 80]
        
        for sentence in sentences:
            normalized = re.sub(r'\s+', ' ', sentence.lower()).strip()
            if normalized in seen_sentences:
                seen_sentences[normalized]["count"] += 1
                if normalized not in [d["text"] for d in duplicated_sentences]:
                    duplicated_sentences.append({
                        "text": normalized,
                        "original": sentence,
                        "sections": [seen_sentences[normalized]["section"], sec.title]
                    })
            else:
                seen_sentences[normalized] = {"count": 1, "section": sec.title}

    if duplicated_sentences:
        details_str = "; ".join([f"\"{d['original'][:50]}...\" duplicated in {d['sections']}" for d in duplicated_sentences[:5]])
        scorecard["text_duplication"] = ValidationMetric(
            status="WARNING",
            message=f"Detected {len(duplicated_sentences)} duplicated text blocks.",
            details=details_str
        )
    else:
        scorecard["text_duplication"] = ValidationMetric(
            status="SUCCESS",
            message="No duplicated text paragraphs detected.",
            details=None
        )

    # 5. Suspicious Empty Pages Check
    empty_pages = []
    doc_pages = getattr(doc, "pages", [])
    doc_figures = getattr(doc, "figures", [])
    doc_tables = getattr(doc, "tables", [])
    doc_equations = getattr(doc, "equations", [])
    doc_algorithms = getattr(doc, "algorithms", [])

    for page_info in doc_pages:
        p_num = getattr(page_info, "page", 1)
        char_count = getattr(page_info, "character_count", 0)
        
        has_fig_or_tab = (
            any(getattr(f, "page", None) == p_num for f in doc_figures) or
            any(getattr(t, "page", None) == p_num for t in doc_tables) or
            any(getattr(eq, "page", None) == p_num for eq in doc_equations) or
            any(getattr(alg, "page", None) == p_num for alg in doc_algorithms)
        )
        
        if char_count < 100 and not has_fig_or_tab:
            empty_pages.append(p_num)
            
    if empty_pages:
        scorecard["empty_pages"] = ValidationMetric(
            status="WARNING",
            message="Suspiciously empty pages detected.",
            details=f"Pages with low text/object coverage: {empty_pages}"
        )
    else:
        scorecard["empty_pages"] = ValidationMetric(
            status="SUCCESS",
            message="All pages have reasonable text/object coverage.",
            details=None
        )

    # 6. References Check
    refs = getattr(doc, "references", [])
    if len(refs) < 3:
        scorecard["references_check"] = ValidationMetric(
            status="WARNING",
            message="Abnormally low bibliography reference count.",
            details=f"Only {len(refs)} references extracted."
        )
    else:
        scorecard["references_check"] = ValidationMetric(
            status="SUCCESS",
            message="Bibliography reference listing is populated.",
            details=f"Extracted {len(refs)} bibliography references."
        )

    # 7. Abnormal Text Coverage Check
    total_pages = len(doc_pages)
    if total_pages > 0:
        total_chars = sum(getattr(p, "character_count", 0) for p in doc_pages)
        avg_coverage = total_chars / total_pages
    else:
        total_chars = sum(len(getattr(s, "content", "")) for s in getattr(doc, "sections", []))
        avg_coverage = total_chars
    
    if avg_coverage < 500:
        scorecard["text_coverage"] = ValidationMetric(
            status="WARNING",
            message="Abnormally low text density per page.",
            details=f"Average density: {avg_coverage:.1f} characters/page. May indicate OCR failure."
        )
    else:
        scorecard["text_coverage"] = ValidationMetric(
            status="SUCCESS",
            message="Text density is normal.",
            details=f"Average density: {avg_coverage:.1f} characters/page."
        )

    # 8. Malformed Tables Check
    malformed_tables = []
    for table in doc_tables:
        t_id = table.get("id", "tbl") if isinstance(table, dict) else getattr(table, "id", "tbl")
        t_md = table.get("content_markdown", "") if isinstance(table, dict) else getattr(table, "content_markdown", "")
        lines = [l.strip() for l in (t_md or "").split('\n') if l.strip()]
        if not lines:
            malformed_tables.append(f"[{t_id}] Table is empty")
            continue
            
        row_widths = []
        for line in lines:
            if re.match(r'^\s*\|?\s*[-:\s|]+\s*\|?\s*$', line):
                continue
            cells = [c.strip() for c in line.split('|')[1:-1]]
            row_widths.append(len(cells))
            
        if len(row_widths) > 1 and len(set(row_widths)) > 1:
            malformed_tables.append(f"[{t_id}] inconsistent cell count: {list(set(row_widths))}")

    if malformed_tables:
        scorecard["malformed_tables"] = ValidationMetric(
            status="WARNING",
            message="Malformed tables detected (row cell mismatch).",
            details=" | ".join(malformed_tables)
        )
    else:
        scorecard["malformed_tables"] = ValidationMetric(
            status="SUCCESS",
            message="All extracted tables are structurally valid.",
            details=None
        )

    # 9. Missing Captions Check
    missing_captions = []
    for fig in doc_figures:
        fig_id = fig.get("id", "fig") if isinstance(fig, dict) else getattr(fig, "id", "fig")
        caption = fig.get("caption", "") if isinstance(fig, dict) else getattr(fig, "caption", "")
        if not caption or len(str(caption).strip()) < 5:
            missing_captions.append(f"Figure [{fig_id}]")
    for table in doc_tables:
        t_id = table.get("id", "tbl") if isinstance(table, dict) else getattr(table, "id", "tbl")
        caption = table.get("caption", "") if isinstance(table, dict) else getattr(table, "caption", "")
        if not caption or len(str(caption).strip()) < 5:
            missing_captions.append(f"Table [{t_id}]")
            
    if missing_captions:
        scorecard["missing_captions"] = ValidationMetric(
            status="WARNING",
            message="Visual objects missing captions.",
            details="; ".join(missing_captions)
        )
    else:
        scorecard["missing_captions"] = ValidationMetric(
            status="SUCCESS",
            message="All figures and tables have captions.",
            details=None
        )

    # Conflict Logging Fallback
    ext_meta = getattr(doc, "extraction_metadata", {})
    conflict_log = ext_meta.get("conflicts", []) if isinstance(ext_meta, dict) else []
    for conf in conflict_log:
        conflicts_logged.append({
            "check": "merger_discrepancy",
            "message": conf.get("message", "Unknown conflict")
        })

    valid = not any(metric.status == "ERROR" for metric in scorecard.values())
    total_metrics = len(scorecard)
    success_metrics = sum(1 for m in scorecard.values() if m.status == "SUCCESS")
    score = round((success_metrics / max(total_metrics, 1)) * 100, 1)

    return ExtractionQualityReport(
        paper_id=getattr(doc, "paper_id", "paper"),
        valid=valid,
        scorecard=scorecard,
        completeness_score=score,
        conflicts_logged=conflicts_logged
    )
