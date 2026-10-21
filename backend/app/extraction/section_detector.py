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


AFFILIATION_KEYWORDS = {
    "department", "dept", "university", "college", "school", "institute", 
    "faculty", "center", "centre", "laboratory", "laboratories", "lab", 
    "hospital", "email", "emails", "@", "india", "usa", "china", "germany",
    "united kingdom", "campus", "author", "contributed", "correspondence", 
    "corresponding", "technology", "sciences", "engineering", "corporation",
    "corp", "inc", "microsoft", "google", "meta", "openai", "amazon", "apple",
    "version", "published"
}

BANNER_PATTERNS = re.compile(
    r'^\s*(vol(?:ume)?[\.\s]?\d|\d{4}\s*[-\u2013]\s*\d{4}|doi\s*:|http[s]?://|copyright\s*©|'
    r'ieee\b|elsevier\b|springer\b|mdpi\b|arxiv\s*:\s*\d|received\b|accepted\b|published\b|'
    r'journal\s+of|proceedings\s+of|transactions\s+on|manuscript\s+id|under\s+review|preprint)',
    re.IGNORECASE
)


def _is_banner_block(text: str) -> bool:
    clean = text.strip()
    if not clean or len(clean) < 4:
        return True
    return bool(BANNER_PATTERNS.search(clean))


def _clean_author_name(name: str) -> Optional[str]:
    # Strip footnote numbers, unicode asterisks (∗ \u2217), daggers, braces, brackets
    n = re.sub(r'[\d\*\†\‡\§\#\u2217\u2020\u2021\{\}\(\)\[\]]+', ' ', name)
    n = re.sub(r'\b(dr|prof|mr|mrs|ms|ph\.?d|m\.?tech|b\.?tech)\.?\s*', '', n, flags=re.IGNORECASE)
    n = re.sub(r'\s+', ' ', n).strip()
    if len(n) < 3 or len(n) > 40:
        return None
    letters = sum(c.isalpha() for c in n)
    if letters < 3:
        return None
    lower = n.lower()
    if any(k in lower for k in [
        "university", "department", "college", "email", "@", "school", "institute",
        "corporation", "corp", "inc", "microsoft", "google", "meta", "openai", "amazon",
        "version", "research", "laborator", "center", "centre"
    ]):
        return None
    # Reject email slugs or fragments
    if "@" in n or "{" in name or "}" in name or ".com" in lower or ".edu" in lower or ".org" in lower:
        return None
    return n.title() if n.isupper() else n


def _extract_frontmatter(pages_data: List[Dict[str, Any]], body_font_size: float) -> Tuple[str, List[str], str, int]:
    """
    Parses Page 1 before the Abstract to extract:
    (title, authors_list, affiliations, abstract_block_idx)
    """
    if not pages_data:
        return "Unknown Title", [], "", -1

    page_1 = pages_data[0]
    blocks = page_1.get("blocks", [])
    if not blocks:
        return "Unknown Title", [], "", -1

    # 1. Locate the Abstract block
    abstract_idx = -1
    for idx, b in enumerate(blocks):
        text = b.get("text", "").strip()
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        first_line = lines[0] if lines else ""
        if ABSTRACT_INLINE_REGEX.match(first_line) or ABSTRACT_ALONE_REGEX.match(first_line):
            abstract_idx = idx
            break
        if re.match(r'^\s*abstract\b', first_line, re.IGNORECASE):
            abstract_idx = idx
            break

    if abstract_idx == -1:
        abstract_idx = min(6, len(blocks))

    front_blocks = blocks[:abstract_idx]
    if not front_blocks:
        return "Unknown Title", [], "", abstract_idx

    # 2. Filter out top banner blocks (e.g. Journal or Conference name)
    valid_blocks = []
    for b in front_blocks:
        if not _is_banner_block(b.get("text", "")):
            valid_blocks.append(b)

    if not valid_blocks:
        valid_blocks = front_blocks

    # 3. Detect multi-line title
    max_font = max((float(b.get("font_size", 10.0)) for b in valid_blocks), default=12.0)
    
    title_blocks = []
    author_blocks = []
    
    found_title_start = False
    for b in valid_blocks:
        b_font = float(b.get("font_size", 10.0))
        is_title_font = b_font >= max(12.5, max_font - 2.5) or (b_font >= 1.25 * body_font_size and max_font >= 13.0)
        
        if is_title_font and not author_blocks:
            found_title_start = True
            title_blocks.append(b)
        elif found_title_start:
            author_blocks.append(b)

    if not title_blocks:
        best_b = max(valid_blocks, key=lambda b: float(b.get("font_size", 0.0)))
        title_blocks = [best_b]
        author_blocks = [b for b in valid_blocks if b != best_b]

    # Assemble complete title
    title_text = " ".join(b.get("text", "").strip() for b in title_blocks)
    title = re.sub(r'\s+', ' ', title_text).strip()
    if not title:
        title = "Unknown Title"

    # 4. Extract Authors and Affiliations
    authors: List[str] = []
    affiliations_parts: List[str] = []

    for ab in author_blocks:
        raw_text = ab.get("text", "").strip()
        lines = [l.strip() for l in raw_text.split("\n") if l.strip()]
        
        hit_affiliation = False
        for line in lines:
            line_lower = line.lower()
            is_affil = (
                hit_affiliation or
                any(kw in line_lower for kw in AFFILIATION_KEYWORDS) or
                "@" in line or "{" in line or "}" in line or
                line.startswith("(") or line.startswith("[") or
                ".com" in line_lower or ".edu" in line_lower or ".org" in line_lower
            )
            if is_affil:
                hit_affiliation = True
                affiliations_parts.append(line)
            else:
                tokens = re.split(r'[,;\t]|\band\b', line, flags=re.IGNORECASE)
                for tok in tokens:
                    c_name = _clean_author_name(tok)
                    if c_name and c_name not in authors:
                        authors.append(c_name)

    if len(authors) <= 1 and author_blocks:
        full_author_raw = "\n".join(ab.get("text", "").strip() for ab in author_blocks)
        pattern_matches = re.findall(r'([A-Za-z\.\s]{3,35}?)(?:[\d\*\†\‡]+(?:\s*,\s*[\d\*\†\‡]+)*|\n|$)', full_author_raw)
        alt_authors = []
        for m in pattern_matches:
            c = _clean_author_name(m)
            if c and c not in alt_authors:
                alt_authors.append(c)
        if len(alt_authors) > len(authors):
            authors = alt_authors

    affiliations = "\n".join(affiliations_parts)
    return title, authors, affiliations, abstract_idx


def _detect_title(pages_data: List[Dict[str, Any]]) -> str:
    """Finds the paper title using frontmatter parser."""
    title, _, _, _ = _extract_frontmatter(pages_data, 10.0)
    return title


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
    body_font_size = _compute_body_font_size(pages_data)
    title, authors, affiliations, abstract_block_idx = _extract_frontmatter(pages_data, body_font_size)
    
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
                
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            if not lines:
                continue
            first_line = lines[0]
            consumed_lines = 1

            # Check if first line is just a section number (e.g. '1', '2', 'IV') with the title on next line
            if (first_line.isdigit() or re.match(r'^[IVXLCDM]+$', first_line) or re.match(r'^\d+(\.\d+)+$', first_line)) and len(lines) > 1:
                combined_cand = f"{first_line}. {lines[1]}"
                h_test, _ = _match_heading_candidate(combined_cand, b, body_font_size)
                if h_test:
                    first_line = combined_cand
                    consumed_lines = 2
            
            # Prior to Abstract, DO NOT trigger arbitrary section titles
            if not abstract_extracted:
                if ABSTRACT_INLINE_REGEX.match(first_line):
                    abstract_body = ABSTRACT_INLINE_REGEX.sub('', text, count=1).strip()
                    add_content("Abstract", None, abstract_body, page_num)
                    abstract_extracted = True
                    current_section = "Abstract"
                    current_subsection = None
                    continue

                heading_candidate, is_major = _match_heading_candidate(first_line, b, body_font_size)
                if heading_candidate and (ABSTRACT_ALONE_REGEX.match(heading_candidate) or "abstract" in heading_candidate.lower()):
                    current_section = "Abstract"
                    current_subsection = None
                    abstract_extracted = True
                    rest_text = "\n".join(lines[consumed_lines:]).strip() if len(lines) > consumed_lines else ""
                    if rest_text:
                        add_content("Abstract", None, rest_text, page_num)
                    continue

                # Front matter block before abstract
                add_content("Metadata / Front Matter", None, text, page_num)
                continue
                
            heading_candidate, is_major = _match_heading_candidate(first_line, b, body_font_size)
                
            if heading_candidate and is_major:
                header_lower = heading_candidate.lower()
                
                if any(kw in header_lower for kw in PRUNE_KEYWORDS):
                    pruning_triggered = True
                    break
                    
                current_section = heading_candidate
                current_subsection = None
                
                rest_text = "\n".join(lines[consumed_lines:]).strip() if len(lines) > consumed_lines else ""
                if rest_text:
                    add_content(current_section, current_subsection, rest_text, page_num)
                    
            elif heading_candidate and not is_major:
                current_subsection = heading_candidate
                rest_text = "\n".join(lines[consumed_lines:]).strip() if len(lines) > consumed_lines else ""
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
        "authors": authors,
        "affiliations": affiliations,
        "sections": sections
    }
