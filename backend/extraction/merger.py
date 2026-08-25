import os
import re
from typing import List, Dict, Any
from core import logger
from schemas import (
    PaperDocument,
    PaperMetadata,
    SectionInfo,
    Section,
    Table,
    Figure,
    Reference,
    PageInfo,
    Provenance,
    Equation,
    Algorithm
)


def _resolve_page_bounds(section_title: str, routed_data: dict) -> tuple:
    """
    Attempts to look up section title occurrences in the inspector's page stats
    or raw parsed sections to determine the start and end page bounds.
    Defaults to (1, 1) if not resolvable.
    """
    # Simple default bounds
    page_start = 1
    page_end = 1
    
    # We can scan the PyMuPDF output if available, as PyMuPDF parses page numbers
    # Alternatively, default to page 1 for abstract/intro and page_count for conclusions
    sec_lower = section_title.lower()
    total_pages = routed_data.get("inspector_report", {}).get("pages", 1)
    
    if "abstract" in sec_lower or "metadata" in sec_lower:
        return 1, 1
    elif "introduction" in sec_lower:
        return 1, min(2, total_pages)
    elif "conclusion" in sec_lower:
        return max(1, total_pages - 1), total_pages
    
    return page_start, page_end


def merge_extractions(routed_data: dict) -> PaperDocument:
    """
    Merges raw routed outputs from PyMuPDF, GROBID, and Docling into a
    single consolidated PaperDocument Pydantic model. Resolves conflicts
    and maps coordinate details.
    """
    paper_id = routed_data["paper_id"]
    filename = routed_data["filename"]
    inspector = routed_data.get("inspector_report", {})
    
    logger.info(f"Merging extraction outputs for '{filename}' into canonical PaperDocument...")

    # 1. Compile PaperMetadata (Prioritize GROBID for metadata fields)
    title = "Unknown Title"
    authors = ["Unknown Author"]
    abstract = ""
    sections_found_infos = []

    grobid_out = routed_data.get("grobid_output")
    pymupdf_out = routed_data.get("pymupdf_output")
    docling_out = routed_data.get("docling_output")

    if grobid_out and grobid_out.get("valid"):
        gr_title = grobid_out.get("title", "").strip()
        if gr_title and gr_title.lower() not in ("unknown title", "unknown", "untitled"):
            title = gr_title
            
        gr_authors = grobid_out.get("authors", [])
        if gr_authors and gr_authors != ["Unknown Author"]:
            authors = gr_authors
            
        gr_abstract = grobid_out.get("abstract", "").strip()
        if gr_abstract:
            abstract = gr_abstract

    # Fallback to PyMuPDF metadata if fields are still empty
    if pymupdf_out:
        if not title or title.lower() in ("unknown title", "unknown", "untitled", ""):
            py_title = pymupdf_out.get("title", "").strip()
            if py_title:
                title = py_title
                
        if not abstract:
            abstract_sec = pymupdf_out.get("sections", {}).get("Abstract")
            if abstract_sec:
                abstract = abstract_sec.get("content", "")

    # Calculate section infos list for metadata
    source_sections = {}
    if grobid_out and grobid_out.get("valid"):
        source_sections = grobid_out.get("sections", {})
    elif pymupdf_out:
        source_sections = pymupdf_out.get("sections", {})

    for sec_title, sec_data in source_sections.items():
        char_len = len(sec_data.get("content", ""))
        sections_found_infos.append(SectionInfo(title=sec_title, character_count=char_len))

    metadata = PaperMetadata(
        title=title,
        authors=authors,
        abstract=abstract,
        sections_found=sections_found_infos,
        primary_contribution="Automated change detection research."
    )

    # 2. Build Section list
    sections_list = []
    for sec_title, sec_data in source_sections.items():
        # Skip Tables metadata section from section prose
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

    # 3. Build Tables list
    tables_list = []
    
    # Check Docling tables first (Docling has highest layout table accuracy)
    if docling_out and docling_out.get("tables"):
        for t_idx, tbl in enumerate(docling_out["tables"]):
            tables_list.append(Table(
                id=f"tab_{t_idx + 1}",
                caption=tbl.get("caption", f"Table {t_idx + 1}"),
                content_markdown=tbl.get("content_markdown", ""),
                page=tbl.get("page", 1)
            ))
            
    # Fallback to pdfplumber tables extracted under PyMuPDF parser
    elif pymupdf_out and "Tables" in pymupdf_out.get("sections", {}):
        pymupdf_tables = pymupdf_out["sections"]["Tables"].get("subsections", {})
        for t_idx, (t_caption, t_markdown) in enumerate(pymupdf_tables.items()):
            tables_list.append(Table(
                id=f"tab_{t_idx + 1}",
                caption=t_caption,
                content_markdown=t_markdown,
                page=1 # default page
            ))
            
    # Fallback to GROBID tables
    elif grobid_out and grobid_out.get("tables"):
        for t_idx, tbl in enumerate(grobid_out["tables"]):
            tables_list.append(Table(
                id=tbl.get("id", f"tab_{t_idx + 1}"),
                caption=tbl.get("caption", f"Table {t_idx + 1}"),
                content_markdown=tbl.get("content", ""),
                page=1 # default
            ))

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

    # Compile all text blocks from all active parsers to prevent missing nested text
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
                
    if docling_out and docling_out.get("markdown"):
        all_text_blocks.append((docling_out["markdown"], 1))

    # 6. Build Equations list (Direct GROBID tags + Regex-based display equation scanner)
    equations_list = []
    seen_equations = set()
    
    # 6a. Standard GROBID parsed equations
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

    # 6b. Regex-based display equation scanner (IEEE style numbered formulas)
    for block, page_num in all_text_blocks:
        if not block:
            continue
        for line in block.split("\n"):
            line = line.strip()
            eq_match = re.search(r'^(.*?)\s*\((\d+[a-z]?)\)\s*$', line)
            if eq_match:
                eq_body = eq_match.group(1).strip()
                eq_num = eq_match.group(2)
                # Ensure it looks like a formula (has operators or mathematical symbols) and is not too long
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
        # Scan for Algorithm headings or inline listings
        for match in re.finditer(r'\b(?:Algorithm|ALGORITHM)\s+([IVX\d]+)\b[^\n]*', block, re.IGNORECASE):
            alg_caption = match.group(0).strip()
            if len(alg_caption) > 10 and alg_caption not in seen_algorithms:
                seen_algorithms.add(alg_caption)
                
                start_idx = match.start()
                end_idx = block.find("\n\n", start_idx)
                if end_idx == -1:
                    end_idx = len(block)
                alg_body = block[start_idx:end_idx].strip()
                
                # Check for common pseudocode markers
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
            width=612.0,  # Standard letter width points
            height=792.0, # Standard letter height points
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
