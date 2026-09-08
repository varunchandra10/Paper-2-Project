import re
from typing import List, Dict, Any, Tuple, Optional
from app.extraction.constants import (
    MAJOR_HEADER_REGEX,
    ROMAN_NUMERAL_HEADER_REGEX,
    NUMBERED_HEADER_REGEX,
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
        if len(text) < 10 or text.lower().startswith("vol") or "arxiv" in text.lower() or "journal" in text.lower():
            continue
            
        if b.get("font_size", 0.0) > max_size:
            max_size = b.get("font_size", 0.0)
            title_text = text
            
    return re.sub(r'\s+', ' ', title_text).strip() if title_text else "Unknown Title"


def _compute_body_font_size(pages_data: List[Dict[str, Any]]) -> float:
    """Calculates median font size across substantial text blocks as body text baseline."""
    sizes = []
    for page in pages_data:
        for b in page.get("blocks", []):
            text = b.get("text", "").strip()
            if len(text) > 25:
                sizes.append(float(b.get("font_size", 10.0)))
    if not sizes:
        return 10.0
    sizes.sort()
    return sizes[len(sizes) // 2]


def _match_major_heading(first_line: str) -> Optional[str]:
    """Matches a line against recognized major section headings."""
    m = MAJOR_HEADER_REGEX.match(first_line.strip())
    return m.group(0).strip() if m else None


def _match_subsection_heading(first_line: str) -> Optional[str]:
    """Matches numbered (e.g. 1.1) or lettered (e.g. A.) subsection headings."""
    line = first_line.strip()
    m = SUBSECTION_NUM_REGEX.match(line)
    if m:
        return f"{m.group(1)} {m.group(2).strip()}"
    m = SUBSECTION_LETTER_REGEX.match(line)
    if m:
        return f"{m.group(1)}. {m.group(2).strip()}"
    return None


def _match_heading_candidate(first_line: str, block: Dict[str, Any], body_font_size: float) -> Tuple[Optional[str], bool]:
    """
    Font-aware section and heading matcher:
    1. Tests standard major headers (Introduction, Method, etc.)
    2. Tests Roman numerals (III. PROPOSED ARCHITECTURE, IV. EXPERIMENTS)
    3. Tests numbered headers with hyphens (2. SYSTEM-DESIGN)
    4. Tests subsections (A. Backbone, 2.1 Setup)
    5. Applies bold & font size heuristics (> 1.1x body) for unnumbered headings.
    Returns (matched_heading, is_major).
    """
    line = first_line.strip()
    if not line or len(line) < 3:
        return None, False

    # 1. Standard major section heading
    m_major = MAJOR_HEADER_REGEX.match(line)
    if m_major:
        return m_major.group(0).strip(), True

    # 2. Roman numeral header (e.g. III. PROPOSED ARCHITECTURE, IV-A. ABLATION)
    m_roman = ROMAN_NUMERAL_HEADER_REGEX.match(line)
    if m_roman:
        return f"{m_roman.group(1)}. {m_roman.group(2).strip()}", True

    # 3. Numbered header with optional hyphens (e.g. 2. SYSTEM-DESIGN)
    m_num = NUMBERED_HEADER_REGEX.match(line)
    if m_num:
        num_str = m_num.group(1)
        if "." in num_str:
            return f"{num_str} {m_num.group(2).strip()}", False
        return f"{num_str}. {m_num.group(2).strip()}", True

    # 4. Standard lettered or decimal subsection
    m_sub = _match_subsection_heading(line)
    if m_sub:
        return m_sub, False

    # 5. Font size and Bold Heuristics for Unnumbered Headings
    font_name = str(block.get("font_name", "")).lower()
    font_size = float(block.get("font_size", 0.0) or 0.0)
    is_bold = any(kw in font_name for kw in ("bold", "black", "cmbx", "heavy", "bolder"))
    is_larger_font = font_size >= (body_font_size * 1.1)

    if (is_bold or is_larger_font) and len(line) <= 85:
        # Must not look like running prose
        if not line.endswith(".") and not line.endswith(",") and not line.endswith(";"):
            if line[0].isupper() and not line.startswith(("-", "*", "•", "(")):
                words = line.split()
                if len(words) <= 10:
                    is_major = is_larger_font or line.isupper()
                    return line, is_major

    return None, False


def detect_sections(pages_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Groups page layout blocks into a structured section tree using font size
    heuristics, Roman numerals, hyphenated titles, and pruning rules.
    """
    title = _detect_title(pages_data)
    body_font_size = _compute_body_font_size(pages_data)
    
    sections = {}
    current_section = "Metadata / Front Matter"
    current_subsection = None
    
    def add_content(sec, sub, text, page_num=1):
        if sec not in sections:
            sections[sec] = {
                "content": "",
                "subsections": {},
                "page_start": page_num,
                "page_end": page_num
            }
        else:
            if "page_start" not in sections[sec]:
                sections[sec]["page_start"] = page_num
            sections[sec]["page_end"] = max(sections[sec].get("page_end", page_num), page_num)

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
            
        page_num = page.get("page", 1)
        blocks = page.get("blocks", [])
        for b in blocks:
            text = b.get("text", "").strip()
            if not text:
                continue
                
            lines = text.split('\n')
            first_line = lines[0].strip()
            
            # Abstract detection
            if not abstract_extracted and ABSTRACT_INLINE_REGEX.match(first_line):
                abstract_body = ABSTRACT_INLINE_REGEX.sub('', text, count=1).strip()
                add_content("Abstract", None, abstract_body, page_num)
                abstract_extracted = True
                continue
                
            heading_candidate, is_major = _match_heading_candidate(first_line, b, body_font_size)
                
            if heading_candidate and is_major:
                header_lower = heading_candidate.lower()
                
                if any(kw in header_lower for kw in PRUNE_KEYWORDS):
                    pruning_triggered = True
                    break
                    
                if ABSTRACT_ALONE_REGEX.match(heading_candidate) and not abstract_extracted:
                    current_section = "Abstract"
                    abstract_extracted = True
                else:
                    current_section = heading_candidate
                    
                current_subsection = None
                
                rest_text = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""
                if rest_text:
                    add_content(current_section, current_subsection, rest_text, page_num)
                    
            elif heading_candidate and not is_major:
                current_subsection = heading_candidate
                rest_text = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""
                if rest_text:
                    add_content(current_section, current_subsection, rest_text, page_num)
            else:
                add_content(current_section, current_subsection, text, page_num)
                
        page_tables = page.get("tables", [])
        for table_name, table_md in page_tables:
            if "Tables" not in sections:
                sections["Tables"] = {"content": "", "subsections": {}}
            sections["Tables"]["subsections"][table_name] = table_md
                
    return {
        "title": title,
        "sections": sections
    }
