"""
Consensus Document Merger for Academic PDFs.

Assembles canonical PaperDocument schemas by merging deterministic PyMuPDF structural text,
targeted VLM element transcriptions (Figures, Tables, Equations), and citation reference lists
with complete source provenance and element-level confidence scores.
"""

import os
import re
from typing import List, Dict, Any, Optional
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
    docling_out: Optional[dict] = None,
    pymupdf_out: Optional[dict] = None,
    gemini_out: Optional[dict] = None
) -> List[Table]:
    """
    Backward-compatible consensus aggregator for tables across multiple parser outputs.
    Normalizes keys and selects richest markdown representation.
    """
    tables_by_key: Dict[str, Table] = {}
    counter = 1

    # 1. Process Gemini / VLM tables
    if isinstance(gemini_out, dict) and gemini_out.get("tables"):
        for tbl in gemini_out.get("tables", []):
            if isinstance(tbl, dict):
                cap = tbl.get("caption", f"Table {counter}")
                md = tbl.get("content_markdown", "")
                page_num = tbl.get("page", 1)
            else:
                cap = f"Table {counter}"
                md = str(tbl)
                page_num = 1
            key = _normalize_table_key(cap, counter)
            tables_by_key[key] = Table(
                id=key,
                caption=cap,
                content_markdown=md,
                page=page_num,
                source={"extraction_method": "gemini_vlm"},
                confidence=0.95
            )
            counter += 1

    # 2. Process Docling tables
    if isinstance(docling_out, dict) and docling_out.get("tables"):
        for tbl in docling_out.get("tables", []):
            if isinstance(tbl, dict):
                cap = tbl.get("caption", f"Table {counter}")
                md = tbl.get("content_markdown", "")
                page_num = tbl.get("page", 1)
            else:
                cap = f"Table {counter}"
                md = str(tbl)
                page_num = 1
            key = _normalize_table_key(cap, counter)

            if key in tables_by_key:
                existing = tables_by_key[key]
                if len(md) > len(existing.content_markdown):
                    existing.content_markdown = md
                if "Table" in cap and len(cap) > len(existing.caption):
                    existing.caption = cap
                if page_num and page_num > 1:
                    existing.page = page_num
            else:
                tables_by_key[key] = Table(
                    id=key,
                    caption=cap,
                    content_markdown=md,
                    page=page_num,
                    source={"extraction_method": "docling_parser"},
                    confidence=0.90
                )
                counter += 1

    # 3. Process PyMuPDF tables
    if isinstance(pymupdf_out, dict) and "sections" in pymupdf_out and "Tables" in pymupdf_out["sections"]:
        tbl_sec = pymupdf_out["sections"]["Tables"]
        sub = tbl_sec.get("subsections", {}) if isinstance(tbl_sec, dict) else {}
        if isinstance(sub, dict):
            for cap, md in sub.items():
                key = _normalize_table_key(cap, counter)
                if key not in tables_by_key:
                    tables_by_key[key] = Table(
                        id=key,
                        caption=cap,
                        content_markdown=str(md),
                        page=1,
                        source={"extraction_method": "pymupdf_parser"},
                        confidence=0.80
                    )
                    counter += 1

    return list(tables_by_key.values())


def _resolve_page_bounds(section_name: str, routed_data: dict) -> tuple:
    """Estimates page start and page end coordinates for a given section."""
    inspector = routed_data.get("inspector_report", {})
    total_pages = inspector.get("pages", 1)
    sec_lower = section_name.lower().strip()

    # Check PyMuPDF section metadata if available
    pymupdf_out = routed_data.get("pymupdf_output", {})
    if isinstance(pymupdf_out, dict):
        sections_dict = pymupdf_out.get("sections", {})
        for s_title, s_data in sections_dict.items():
            clean_s_title = re.sub(r'^\s*(?:\d+|[ivxlcdm]+)\.?\s*', '', s_title.lower()).strip()
            clean_target = re.sub(r'^\s*(?:\d+|[ivxlcdm]+)\.?\s*', '', sec_lower).strip()
            if s_title.lower() == sec_lower or clean_s_title == clean_target or clean_target in clean_s_title:
                if isinstance(s_data, dict) and "page_start" in s_data:
                    return s_data.get("page_start", 1), s_data.get("page_end", total_pages)

    if "abstract" in sec_lower or "metadata" in sec_lower:
        return 1, 1
    elif "introduction" in sec_lower:
        return 1, min(2, total_pages)
    elif "conclusion" in sec_lower or "reference" in sec_lower:
        return max(1, total_pages - 1), total_pages

    return 1, total_pages



def merge_extractions(routed_data: dict) -> PaperDocument:
    """
    Merges deterministic PyMuPDF layout, targeted VLM elements, and standby parsers
    into a unified, fully-provenanced PaperDocument.
    """
    paper_id = routed_data["paper_id"]
    filename = routed_data["filename"]
    inspector = routed_data.get("inspector_report", {})

    pymupdf_out = routed_data.get("pymupdf_output")
    vlm_elements = routed_data.get("vlm_elements", {})
    candidates = routed_data.get("element_candidates", {})
    grobid_out = routed_data.get("grobid_output")
    docling_out = routed_data.get("docling_output")
    gemini_out = routed_data.get("gemini_output")

    # ── 1. Compile PaperMetadata ──
    title = "Unknown Title"
    authors = ["Unknown Author"]
    abstract = ""
    sections_found_infos = []

    if pymupdf_out:
        py_title = pymupdf_out.get("title", "").strip()
        if py_title and py_title.lower() not in ("unknown title", "untitled"):
            title = py_title
        py_authors = pymupdf_out.get("authors", [])
        if py_authors and (authors == ["Unknown Author"] or not authors):
            authors = py_authors
        abstract_sec = pymupdf_out.get("sections", {}).get("Abstract")
        if abstract_sec:
            abstract = abstract_sec.get("content", "") if isinstance(abstract_sec, dict) else str(abstract_sec)

    if gemini_out and gemini_out.get("valid"):
        gm_title = gemini_out.get("title", "").strip()
        if gm_title and title in ("Unknown Title", "untitled", ""):
            title = gm_title
        gm_authors = gemini_out.get("authors", [])
        if gm_authors and gm_authors != ["Unknown Author"]:
            authors = gm_authors
        if not abstract and gemini_out.get("abstract"):
            abstract = gemini_out.get("abstract", "")

    if grobid_out and grobid_out.get("valid"):
        gr_title = grobid_out.get("title", "").strip()
        if gr_title and title in ("Unknown Title", "untitled"):
            title = gr_title
        gr_authors = grobid_out.get("authors", [])
        if gr_authors and gr_authors != ["Unknown Author"]:
            authors = gr_authors
        if not abstract:
            abstract = grobid_out.get("abstract", "")

    # Fallback to filename if title remains unextracted
    if not title or title.lower() in ("unknown title", "untitled", ""):
        base_name = os.path.splitext(filename)[0]
        title = base_name.replace("_", " ").title()

    # ── 2. Build Sections List ──
    sections_list = []
    source_sections = {}
    if pymupdf_out and pymupdf_out.get("sections"):
        source_sections = pymupdf_out["sections"]
    elif gemini_out and gemini_out.get("sections"):
        source_sections = gemini_out["sections"]
    elif grobid_out and grobid_out.get("sections"):
        source_sections = grobid_out["sections"]

    for sec_title, sec_data in source_sections.items():
        if sec_title.lower() in ("tables", "figures"):
            continue
        p_start, p_end = _resolve_page_bounds(sec_title, routed_data)
        if isinstance(sec_data, dict):
            content = sec_data.get("content", "").strip()
            subsections = sec_data.get("subsections", {})
        else:
            content = str(sec_data).strip()
            subsections = {}

        sections_list.append(
            Section(
                title=sec_title,
                content=content,
                subsections=subsections,
                page_start=p_start,
                page_end=p_end,
                source={"page": p_start, "extraction_method": "pymupdf_deterministic"},
                confidence=0.98 if content else 0.50
            )
        )
        sections_found_infos.append(SectionInfo(title=sec_title, character_count=len(content)))

    metadata = PaperMetadata(
        title=title,
        authors=authors,
        abstract=abstract,
        sections_found=sections_found_infos
    )

    # ── 3. Assemble Figures List (VLM Output + Deterministic Crops) ──
    figures_list: List[Figure] = []
    seen_fig_ids = set()

    # Priority 1: VLM analyzed figures
    # ── 3. Assemble Figures List (VLM Output + Deterministic Crops) ──
    figures_list: List[Figure] = []
    seen_fig_ids = set()

    # Priority 1: VLM analyzed figures
    for fig in vlm_elements.get("figures", []):
        f_id = fig.get("element_id", f"fig_{len(figures_list) + 1}")
        if f_id not in seen_fig_ids:
            seen_fig_ids.add(f_id)
            figures_list.append(
                Figure(
                    id=f_id,
                    caption=fig.get("caption", ""),
                    page=fig.get("page", 1),
                    visual_description=fig.get("visual_description"),
                    image_path=fig.get("image_path"),
                    components=fig.get("components", []),
                    relationships=fig.get("relationships", []),
                    source={"extraction_method": "gemini_vlm", "source_image": fig.get("image_path"), "vlm_used": True},
                    vlm_used=True,
                    confidence=fig.get("confidence", 0.92)
                )
            )

    # Priority 2: Candidates preserved without VLM (offline or plain figures)
    for fig in candidates.get("figures", []):
        f_id = fig.get("element_id", f"fig_{len(figures_list) + 1}")
        if f_id not in seen_fig_ids:
            seen_fig_ids.add(f_id)
            figures_list.append(
                Figure(
                    id=f_id,
                    caption=fig.get("caption", ""),
                    page=fig.get("page", 1),
                    visual_description=None,  # Never claim visual understanding when VLM was skipped
                    image_path=fig.get("image_path"),
                    source={
                        "extraction_method": "pymupdf_cropper",
                        "bbox": fig.get("bbox"),
                        "vlm_used": False,
                        "reason": "deterministic_preservation_sufficient"
                    },
                    vlm_used=False,
                    confidence=0.85
                )
            )

    # ── 4. Assemble Tables List (VLM Markdown + Deterministic Tables) ──
    tables_list: List[Table] = []
    seen_tab_ids = set()

    # Priority 1: VLM formatted Markdown tables
    for tab in vlm_elements.get("tables", []):
        t_id = tab.get("element_id", f"table_{len(tables_list) + 1}")
        if t_id not in seen_tab_ids:
            seen_tab_ids.add(t_id)
            tables_list.append(
                Table(
                    id=t_id,
                    caption=tab.get("caption", ""),
                    content_markdown=tab.get("content_markdown", ""),
                    headers=tab.get("headers", []),
                    rows=tab.get("rows", []),
                    page=tab.get("page", 1),
                    source={"extraction_method": "gemini_vlm", "source_image": tab.get("image_path"), "vlm_used": True},
                    vlm_used=True,
                    confidence=tab.get("confidence", 0.95)
                )
            )

    # Priority 2: Docling & PyMuPDF layout tables
    if isinstance(docling_out, dict) and docling_out.get("tables"):
        for idx, tbl in enumerate(docling_out.get("tables", [])):
            t_id = f"table_{len(tables_list) + 1}"
            if t_id not in seen_tab_ids:
                seen_tab_ids.add(t_id)
                cap = tbl.get("caption") if isinstance(tbl, dict) else f"Table {idx + 1}"
                md = tbl.get("content_markdown", "") if isinstance(tbl, dict) else str(tbl)
                page_num = tbl.get("page", 1) if isinstance(tbl, dict) else 1
                tables_list.append(
                    Table(
                        id=t_id,
                        caption=cap or f"Table {idx + 1}",
                        content_markdown=md,
                        page=page_num,
                        source={"extraction_method": "docling_parser", "vlm_used": False},
                        vlm_used=False,
                        confidence=0.90
                    )
                )

    # Priority 3: Candidates preserved deterministically
    for tab in candidates.get("tables", []):
        t_id = tab.get("element_id", f"table_{len(tables_list) + 1}")
        if t_id not in seen_tab_ids:
            seen_tab_ids.add(t_id)
            tables_list.append(
                Table(
                    id=t_id,
                    caption=tab.get("caption", ""),
                    content_markdown=tab.get("content_text", ""),
                    page=tab.get("page", 1),
                    source={
                        "extraction_method": "pymupdf_cropper",
                        "bbox": tab.get("bbox"),
                        "vlm_used": False,
                        "reason": "deterministic_table_sufficient"
                    },
                    vlm_used=False,
                    confidence=0.80
                )
            )

    # ── 5. Assemble Equations List (VLM LaTeX + Heuristic Math) ──
    equations_list: List[Equation] = []
    seen_eq_ids = set()

    # Priority 1: VLM LaTeX equations
    for eq in vlm_elements.get("equations", []):
        e_id = eq.get("element_id", f"eq_{len(equations_list) + 1}")
        if e_id not in seen_eq_ids:
            seen_eq_ids.add(e_id)
            equations_list.append(
                Equation(
                    id=e_id,
                    latex=eq.get("latex", ""),
                    caption=eq.get("caption"),
                    variables=eq.get("variables", []),
                    page=eq.get("page", 1),
                    source={"extraction_method": "gemini_vlm", "vlm_used": True},
                    vlm_used=True,
                    confidence=eq.get("confidence", 0.92)
                )
            )

    # Priority 2: Candidates preserved from layout
    for eq in candidates.get("equations", []):
        e_id = eq.get("element_id", f"eq_{len(equations_list) + 1}")
        if e_id not in seen_eq_ids:
            seen_eq_ids.add(e_id)
            equations_list.append(
                Equation(
                    id=e_id,
                    latex=eq.get("content_text", ""),
                    caption=eq.get("caption"),
                    page=eq.get("page", 1),
                    source={
                        "extraction_method": "pymupdf_cropper",
                        "bbox": eq.get("bbox"),
                        "vlm_used": False,
                        "reason": "deterministic_ascii_math_sufficient"
                    },
                    vlm_used=False,
                    confidence=0.80
                )
            )


    # ── 6. Assemble References List ──
    references_list: List[Reference] = []
    if isinstance(grobid_out, dict) and grobid_out.get("references"):
        for r_idx, ref in enumerate(grobid_out.get("references", [])):
            if isinstance(ref, dict):
                ref_id = ref.get("id") or str(r_idx + 1)
                cit_text = ref.get("raw_text") or ref.get("title", "")
            else:
                ref_id = str(r_idx + 1)
                cit_text = str(ref)
            references_list.append(
                Reference(
                    ref_id=ref_id,
                    citation_text=cit_text
                )
            )
    elif pymupdf_out and "References" in pymupdf_out.get("sections", {}):
        ref_sec = pymupdf_out["sections"]["References"]
        ref_text = ref_sec.get("content", "") if isinstance(ref_sec, dict) else str(ref_sec)
        for idx, line in enumerate(ref_text.split("\n")):
            line_s = line.strip()
            if len(line_s) > 20:
                references_list.append(
                    Reference(ref_id=str(idx + 1), citation_text=line_s)
                )

    # ── 7. Assemble PageInfo List ──
    pages_list = []
    total_pages_count = inspector.get("pages", 1)
    avg_chars = int(inspector.get("text_coverage_chars", 0) / total_pages_count) if total_pages_count > 0 else 0
    for p_num in range(1, total_pages_count + 1):
        pages_list.append(
            PageInfo(page=p_num, width=612.0, height=792.0, character_count=avg_chars)
        )

    # ── 8. Create Extraction Metadata with Timing, Complexity & VLM Provenance ──
    extraction_meta = {
        "layout_type": "scanned" if inspector.get("is_scanned") else "digital",
        "selected_parsers": routed_data.get("selected_parsers", []),
        "timing_metrics": routed_data.get("timing_metrics", {}),
        "vlm_usage": routed_data.get("vlm_usage", {}),
        "complexity_profile": inspector.get("complexity_profile", {}),
        "instrumentation": routed_data.get("instrumentation", {}),
        "conflicts": []
    }

    paper_doc = PaperDocument(
        paper_id=paper_id,
        metadata=metadata,
        sections=sections_list,
        figures=figures_list,
        tables=tables_list,
        equations=equations_list,
        algorithms=[],
        citations=[],
        references=references_list,
        pages=pages_list,
        extraction_metadata=extraction_meta
    )

    return paper_doc

