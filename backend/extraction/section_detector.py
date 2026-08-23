import re
from typing import List, Dict, Any
from core import logger
from extraction.pymupdf_parser import (
    MAJOR_HEADER_REGEX,
    ABSTRACT_INLINE_REGEX,
    ABSTRACT_ALONE_REGEX,
    SUBSECTION_NUM_REGEX,
    SUBSECTION_LETTER_REGEX,
    PRUNE_KEYWORDS
)


def _detect_title(pages_data: List[Dict[str, Any]]) -> str:
    """Finds the paper title using font size heuristics on page 1."""
    if not pages_data:
        return "Unknown Title"
    
    page_1 = pages_data[0]
    blocks = page_1.get("blocks", [])
    if not blocks:
        return "Unknown Title"
        
    max_size = 0.0
    title_text = ""
    
    for b in blocks:
        text = b["text"].strip()
        # Skip small text blocks, metadata labels, and arXiv headers
        if len(text) < 10 or text.lower().startswith("vol") or "arxiv" in text.lower() or "journal" in text.lower():
            continue
            
        if b["font_size"] > max_size:
            max_size = b["font_size"]
            title_text = text
            
    # Clean newlines from title
    return re.sub(r'\s+', ' ', title_text).strip() if title_text else "Unknown Title"


def _match_major_heading(first_line: str):
    m = MAJOR_HEADER_REGEX.match(first_line.strip())
    return m.group(0).strip() if m else None


def _match_subsection_heading(first_line: str):
    line = first_line.strip()
    m = SUBSECTION_NUM_REGEX.match(line)
    if m:
        return f"{m.group(1)} {m.group(2).strip()}"
    m = SUBSECTION_LETTER_REGEX.match(line)
    if m:
        return f"{m.group(1)}. {m.group(2).strip()}"
    return None


def detect_sections(pages_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Groups page layout blocks into a structured section tree.
    Filters out references, bibliography, and acknowledgments using pruning keyword rules.
    """
    title = _detect_title(pages_data)
    logger.info(f"Detecting sections for paper: '{title}'...")
    
    sections = {}
    current_section = "Metadata / Front Matter"
    current_subsection = None
    
    def add_content(sec, sub, text):
        if sec not in sections:
            sections[sec] = {"content": "", "subsections": {}}
        if sub is None:
            existing = sections[sec]["content"]
            sections[sec]["content"] = (existing + "\n\n" + text) if existing else text
        else:
            subs = sections[sec]["subsections"]
            subs[sub] = (subs[sub] + "\n\n" + text) if sub in subs else text

    abstract_extracted = False
    pruning_triggered = False

    for page in pages_data:
        if pruning_triggered:
            break
            
        blocks = page.get("blocks", [])
        for b in blocks:
            text = b["text"].strip()
            if not text:
                continue
                
            lines = text.split('\n')
            first_line = lines[0].strip()
            
            # Inline Abstract check
            if not abstract_extracted and ABSTRACT_INLINE_REGEX.match(first_line):
                abstract_body = ABSTRACT_INLINE_REGEX.sub('', text, count=1).strip()
                add_content("Abstract", None, abstract_body)
                abstract_extracted = True
                continue
                
            major_title = _match_major_heading(first_line)
            sub_title = None
            if not major_title:
                sub_title = _match_subsection_heading(first_line)
                
            if major_title:
                header_lower = major_title.lower()
                
                # Check pruning keywords to skip References/Bibliography
                if any(kw in header_lower for kw in PRUNE_KEYWORDS):
                    pruning_triggered = True
                    logger.info(f"Section pruning triggered by header: '{major_title}'")
                    break
                    
                if ABSTRACT_ALONE_REGEX.match(major_title) and not abstract_extracted:
                    current_section = "Abstract"
                    abstract_extracted = True
                else:
                    current_section = major_title
                    
                current_subsection = None
                
                # Buffer the rest of the block if there are multiple lines
                rest_text = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""
                if rest_text:
                    add_content(current_section, current_subsection, rest_text)
                    
            elif sub_title:
                current_subsection = sub_title
                rest_text = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""
                if rest_text:
                    add_content(current_section, current_subsection, rest_text)
                # Regular paragraph text block
                add_content(current_section, current_subsection, text)
                
        # Group page-level extracted tables into the sections mapping
        page_tables = page.get("tables", [])
        for table_name, table_md in page_tables:
            if "Tables" not in sections:
                sections["Tables"] = {"content": "", "subsections": {}}
            sections["Tables"]["subsections"][table_name] = table_md
                
    return {
        "title": title,
        "sections": sections
    }
