import os
import re
from typing import List, Dict, Any
from app.schemas.canonical_paper import (
    PaperDocument,
    Section,
    Table,
    Figure,
    Reference,
    PageInfo,
    Provenance,
    Equation,
    Algorithm
)
from app.schemas.pipeline_schemas import PaperMetadata, SectionInfo


def _normalize_table_key(caption: str, fallback_index: int) -> str:
    """Normalizes table captions (e.g. 'Table 1: Acc', 'TABLE I', 'Table 2.1') to a canonical key."""
    if not caption:
        return f"table_{fallback_index}"
    m = re.search(r'\b(?:table|tab\.?)\s*([0-9ivxlcdm]+(?:\.[0-9]+)?)', caption, re.IGNORECASE)
    if m:
        num = m.group(1).lower()
        roman_map = {"i": "1", "ii": "2", "iii": "3", "iv": "4", "v": "5", "vi": "6", "vii": "7", "viii": "8", "ix": "9", "x": "10"}
        num = roman_map.get(num, num)
        return f"table_{num}"
    slug = re.sub(r'[^a-zA-Z0-9]', '', caption).lower()
    return slug[:30] if slug else f"table_{fallback_index}"


def extract_consensus_tables(
    docling_out: dict = None,
    pymupdf_out: dict = None,
    gemini_out: dict = None,
    grobid_out: dict = None
) -> List[Table]:
    """
    Consensus Table Union: Matches tables across Docling, Gemini, PyMuPDF,
    and GROBID by normalized caption (e.g. 'Table 1', 'Table 2') and preserves
    all unique tables without greedy if/elif dropping.
    """
    table_candidates = []

    # 1. Docling candidates (high-fidelity visual table structures)
    if docling_out and docling_out.get("tables"):
        for idx, tbl in enumerate(docling_out["tables"]):
            table_candidates.append({
                "source": "docling",
                "caption": tbl.get("caption") or f"Table {idx + 1}",
                "content": tbl.get("content_markdown", ""),
                "page": tbl.get("page", 1)
            })

    # 2. Gemini candidates (deep semantic paper extraction)
    if gemini_out and gemini_out.get("tables"):
        for idx, tbl in enumerate(gemini_out["tables"]):
            table_candidates.append({
                "source": "gemini",
                "caption": tbl.get("caption") or f"Table {idx + 1}",
                "content": tbl.get("content_markdown", "") or tbl.get("content", ""),
                "page": tbl.get("page", 1)
            })

    # 3. PyMuPDF candidates (local layout-extracted tables)
    if pymupdf_out and "Tables" in pymupdf_out.get("sections", {}):
        pymupdf_tables = pymupdf_out["sections"]["Tables"].get("subsections", {})
        for idx, (t_caption, t_markdown) in enumerate(pymupdf_tables.items()):
            table_candidates.append({
                "source": "pymupdf",
                "caption": t_caption or f"Table {idx + 1}",
                "content": t_markdown,
                "page": 1
            })

    # 4. GROBID candidates (standby parser)
    if grobid_out and grobid_out.get("tables"):
        for idx, tbl in enumerate(grobid_out["tables"]):
            table_candidates.append({
                "source": "grobid",
                "caption": tbl.get("caption") or f"Table {idx + 1}",
                "content": tbl.get("content", ""),
                "page": tbl.get("page", 1)
            })

    merged: Dict[str, Dict[str, Any]] = {}

    for idx, cand in enumerate(table_candidates):
        key = _normalize_table_key(cand["caption"], idx + 1)
        if key not in merged:
            merged[key] = {
                "id": f"tab_{len(merged) + 1}",
                "caption": cand["caption"],
                "content_markdown": cand["content"],
                "page": cand["page"]
            }
        else:
            existing = merged[key]
            # Prefer richer markdown tables over brief stubs
            if len(cand["content"]) > len(existing["content_markdown"]) and "|" in cand["content"]:
                existing["content_markdown"] = cand["content"]
            # Prefer descriptive caption over generic "Table X"
            if len(cand["caption"]) > len(existing["caption"]) and not existing["caption"].lower().startswith(cand["caption"].lower()):
                existing["caption"] = cand["caption"]
            # Update page number if candidate has non-default page
            if existing["page"] == 1 and cand["page"] > 1:
                existing["page"] = cand["page"]

    return [
        Table(
            id=t["id"],
            caption=t["caption"],
            content_markdown=t["content_markdown"],
            page=t["page"]
        )
        for t in merged.values()
    ]


def _resolve_page_bounds(section_title: str, routed_data: dict) -> tuple:
    """
    Looks up actual source block page numbers from PyMuPDF layout metadata
    so sections report real page coordinates instead of dummy (1, 1).
    """
    sec_lower = section_title.lower().strip()
    sec_norm = re.sub(r'[^a-zA-Z0-9]', '', sec_lower)
    total_pages = routed_data.get("inspector_report", {}).get("pages", 1)
    
    pymupdf_out = routed_data.get("pymupdf_output") or {}
    py_sections = pymupdf_out.get("sections") or {}

    # 1. Match section in PyMuPDF sections layout metadata
    for p_title, p_data in py_sections.items():
        if p_title.lower() == "tables":
            continue
        p_norm = re.sub(r'[^a-zA-Z0-9]', '', p_title).lower()
        if sec_norm == p_norm or (p_norm and p_norm in sec_norm) or (sec_norm and sec_norm in p_norm):
            p_start = p_data.get("page_start")
            p_end = p_data.get("page_end")
            if p_start is not None and p_end is not None:
                return max(1, int(p_start)), max(int(p_start), min(total_pages, int(p_end)))

    # 2. Match directly against document blocks if present
    doc_pages = routed_data.get("document_blocks") or []
    for p in doc_pages:
        p_num = p.get("page", 1)
        for b in p.get("blocks", []):
            b_text = b.get("text", "").lower()
            if sec_lower in b_text:
                return max(1, p_num), min(total_pages, p_num)

    # 3. Positional fallbacks for known sections
    if "abstract" in sec_lower or "metadata" in sec_lower:
        return 1, 1
    elif "introduction" in sec_lower:
        return 1, min(2, total_pages)
    elif "conclusion" in sec_lower:
        return max(1, total_pages - 1), total_pages
    
    return 1, 1


def merge_extractions(routed_data: dict) -> PaperDocument:
    """
    Merges raw routed outputs from PyMuPDF, GROBID, and Docling into a
    single consolidated PaperDocument Pydantic model. Resolves conflicts
    and maps coordinate details.
    """
    paper_id = routed_data["paper_id"]
    filename = routed_data["filename"]
    inspector = routed_data.get("inspector_report", {})

    gemini_out = routed_data.get("gemini_output")
    grobid_out = routed_data.get("grobid_output")
    pymupdf_out = routed_data.get("pymupdf_output")
    docling_out = routed_data.get("docling_output")

    # =========================================================================
    # [STREAM 2 WEIGHTAGE]: PRIMARY WEIGHTAGE GIVEN TO GOOGLE GEMINI EXTRACTION
    # If Google Gemini succeeded, its complete text, sections, title, authors,
    # and LaTeX equations form the primary spine. PyMuPDF & Docling fill gaps.
    # =========================================================================

    # 1. Compile PaperMetadata (Google Gemini > GROBID > PyMuPDF)
    title = "Unknown Title"
    authors = ["Unknown Author"]
    abstract = ""
    sections_found_infos = []

    # Primary Weightage: Google Gemini 2.0 Flash
    if gemini_out and gemini_out.get("valid"):
        gm_title = gemini_out.get("title", "").strip()
        if gm_title and gm_title.lower() not in ("unknown title", "unknown", "untitled"):
            title = gm_title
        gm_authors = gemini_out.get("authors", [])
        if gm_authors and gm_authors != ["Unknown Author"]:
            authors = gm_authors
        gm_abstract = gemini_out.get("abstract", "").strip()
        if gm_abstract:
            abstract = gm_abstract

    # Fallback to GROBID (standby) if metadata not yet populated
    if not title or title.lower() in ("unknown title", "unknown", "untitled", ""):
        if grobid_out and grobid_out.get("valid"):
            gr_title = grobid_out.get("title", "").strip()
            if gr_title and gr_title.lower() not in ("unknown title", "unknown", "untitled"):
                title = gr_title
            gr_authors = grobid_out.get("authors", [])
            if gr_authors and gr_authors != ["Unknown Author"]:
                authors = gr_authors
            gr_abstract = grobid_out.get("abstract", "").strip()
            if gr_abstract and not abstract:
                abstract = gr_abstract

    # Fallback to PyMuPDF heuristics if still missing
    if pymupdf_out:
        if not title or title.lower() in ("unknown title", "unknown", "untitled", ""):
            py_title = pymupdf_out.get("title", "").strip()
            if py_title:
                title = py_title
        if not abstract:
            abstract_sec = pymupdf_out.get("sections", {}).get("Abstract")
            if abstract_sec:
                abstract = abstract_sec.get("content", "")

    # Source Sections: Primary Weightage to Gemini, with bi-directional gap filling
    source_sections = {}
    if gemini_out and gemini_out.get("valid") and gemini_out.get("sections"):
        source_sections = dict(gemini_out.get("sections", {}))
        # Bi-directional fill: If PyMuPDF detected any major section missing in Gemini, fill it in
        if pymupdf_out and pymupdf_out.get("sections"):
            for py_sec, py_data in pymupdf_out["sections"].items():
                if py_sec.lower() == "tables":
                    continue
                norm_py = re.sub(r'[^a-zA-Z0-9]', '', py_sec).lower()
                already_exists = any(norm_py == re.sub(r'[^a-zA-Z0-9]', '', gs).lower() for gs in source_sections.keys())
                if not already_exists:
                    source_sections[py_sec] = py_data
    elif grobid_out and grobid_out.get("valid"):
        source_sections = dict(grobid_out.get("sections", {}))
    elif pymupdf_out:
        source_sections = dict(pymupdf_out.get("sections", {}))

    for sec_title, sec_data in source_sections.items():
        char_len = len(sec_data.get("content", ""))
        sections_found_infos.append(SectionInfo(title=sec_title, character_count=char_len))

    metadata = PaperMetadata(
        title=title,
        authors=authors,
        abstract=abstract,
        sections_found=sections_found_infos,
        primary_contribution="Automated change detection & deep learning analysis."
    )

    # 2. Build Section list
    sections_list = []
    for sec_title, sec_data in source_sections.items():
        if sec_title.lower() == "tables":
            continue
            
        p_start, p_end = _resolve_page_bounds(sec_title, routed_data)
        sections_list.append(Section(
            title=sec_title,
            content=sec_data.get("content", ""),
            subsections={k: v for k, v in sec_data.get("subsections", {}).items()},
            page_start=p_start,
            page_end=p_end
        ))

    # 3. Build Tables list (Consensus Table Union across Docling, Gemini, PyMuPDF, and GROBID)
    tables_list = extract_consensus_tables(
        docling_out=docling_out,
        pymupdf_out=pymupdf_out,
        gemini_out=gemini_out,
        grobid_out=grobid_out
    )

    # 4. Build Figures list
    figures_list = []
    if grobid_out and grobid_out.get("figures"):
        for fig in grobid_out["figures"]:
            figures_list.append(Figure(
                id=fig.get("id", "fig_unknown"),
                caption=fig.get("caption", "Figure"),
                page=1
            ))
    elif docling_out and docling_out.get("figures"):
        for f_idx, fig in enumerate(docling_out["figures"]):
            figures_list.append(Figure(
                id=f"fig_{f_idx + 1}",
                caption=fig.get("caption", "Figure"),
                page=fig.get("page", 1)
            ))

    # 5. Build Reference bibliography list
    references_list = []
    if grobid_out and grobid_out.get("references"):
        for r_idx, ref in enumerate(grobid_out["references"]):
            references_list.append(Reference(
                ref_id=str(r_idx + 1),
                citation_text=ref
            ))

    all_text_blocks = []
    if pymupdf_out and pymupdf_out.get("sections"):
        for sec_title, sec_data in pymupdf_out["sections"].items():
            p_start, _ = _resolve_page_bounds(sec_title, routed_data)
            all_text_blocks.append((sec_data.get("content", ""), p_start))
            for sub_text in sec_data.get("subsections", {}).values():
                all_text_blocks.append((sub_text, p_start))
                
    if grobid_out and grobid_out.get("sections"):
        for sec_title, sec_data in grobid_out["sections"].items():
            p_start, _ = _resolve_page_bounds(sec_title, routed_data)
            all_text_blocks.append((sec_data.get("content", ""), p_start))
            for sub_text in sec_data.get("subsections", {}).values():
                all_text_blocks.append((sub_text, p_start))

    # 6. Build Equations list (Primary Weightage: Google Gemini LaTeX > GROBID > Regex)
    equations_list = []
    seen_equations = set()
    
    # Primary Weightage: Google Gemini extracted LaTeX formulas
    if gemini_out and gemini_out.get("equations"):
        for eq_idx, eq in enumerate(gemini_out["equations"]):
            eq_body = eq.get("latex", "").strip()
            if eq_body and eq_body not in seen_equations:
                seen_equations.add(eq_body)
                equations_list.append(Equation(
                    id=eq.get("id", f"eq_{len(equations_list) + 1}"),
                    latex=eq_body,
                    page=1,
                    caption=eq.get("caption", f"Equation {len(equations_list) + 1}")
                ))

    # Cross-fill from GROBID (if active on standby)
    if grobid_out and grobid_out.get("equations"):
        for eq_idx, eq in enumerate(grobid_out["equations"]):
            eq_body = eq.get("latex", "").strip()
            if eq_body and eq_body not in seen_equations:
                seen_equations.add(eq_body)
                equations_list.append(Equation(
                    id=eq.get("id", f"eq_{len(equations_list) + 1}"),
                    latex=eq_body,
                    page=1,
                    caption=eq.get("caption")
                ))

    for block, page_num in all_text_blocks:
        if not block:
            continue
        for line in block.split("\n"):
            line = line.strip()
            eq_match = re.search(r'^(.*?)\s*\((\d+[a-z]?)\)\s*$', line)
            if eq_match:
                eq_body = eq_match.group(1).strip()
                eq_num = eq_match.group(2)
                math_chars = ('=', '+', '-', '*', '/', '^', '_', '\\', 'σ', 'α', 'β', 'λ', 'θ', 'ŷ', '∈', '≈', '×', '∑', '∫', '∆', 'δ', 'µ', '←', '→', '≤', '≥', '±')
                if (0 < len(eq_body) < 150 and 
                        any(c in eq_body for c in math_chars) and 
                        eq_body not in seen_equations):
                    seen_equations.add(eq_body)
                    equations_list.append(Equation(
                        id=f"eq_{len(equations_list) + 1}",
                        latex=eq_body,
                        page=page_num,
                        caption=f"Equation ({eq_num})"
                    ))

    # 7. Build Algorithms list
    algorithms_list = []
    alg_idx = 1
    seen_algorithms = set()
    
    for block, page_num in all_text_blocks:
        if not block:
            continue
        for match in re.finditer(r'\b(?:Algorithm|ALGORITHM)\s+([IVX\d]+)\b[^\n]*', block, re.IGNORECASE):
            alg_caption = match.group(0).strip()
            if len(alg_caption) > 10 and alg_caption not in seen_algorithms:
                seen_algorithms.add(alg_caption)
                start_idx = match.start()
                end_idx = block.find("\n\n", start_idx)
                if end_idx == -1:
                    end_idx = len(block)
                alg_body = block[start_idx:end_idx].strip()
                alg_keywords = ("input", "output", "initialize", "for ", "loop", "if ", "while", "return", "end", "begin", "repeat", "←", "→")
                alg_body_lower = alg_body.lower()
                if any(kw in alg_body_lower for kw in alg_keywords):
                    algorithms_list.append(Algorithm(
                        id=f"alg_{alg_idx}",
                        caption=alg_caption,
                        pseudocode=alg_body,
                        page=page_num
                    ))
                    alg_idx += 1

    # 8. Build PageInfo details
    pages_list = []
    total_pages_count = inspector.get("pages", 1)
    avg_chars_per_page = int(inspector.get("text_coverage_chars", 0) / total_pages_count) if total_pages_count > 0 else 0
    
    for p_num in range(1, total_pages_count + 1):
        pages_list.append(PageInfo(
            page=p_num,
            width=612.0,
            height=792.0,
            character_count=avg_chars_per_page
        ))

    # 9. Record Conflicts
    conflicts = []
    py_title = pymupdf_out.get("title", "") if pymupdf_out else ""
    gr_title = grobid_out.get("title", "") if grobid_out else ""
    
    if py_title and gr_title and py_title.lower() != gr_title.lower():
        conflicts.append({
            "type": "title_mismatch",
            "message": f"PyMuPDF title: '{py_title}' vs. GROBID title: '{gr_title}'"
        })

    extraction_meta = {
        "layout_type": inspector.get("is_scanned", False),
        "selected_parsers": routed_data.get("selected_parsers", []),
        "conflicts": conflicts
    }

    # 10. Create validated PaperDocument
    paper_doc = PaperDocument(
        paper_id=paper_id,
        metadata=metadata,
        sections=sections_list,
        figures=figures_list,
        tables=tables_list,
        equations=equations_list,
        algorithms=algorithms_list,
        citations=[],
        references=references_list,
        pages=pages_list,
        extraction_metadata=extraction_meta
    )
    
    return paper_doc
