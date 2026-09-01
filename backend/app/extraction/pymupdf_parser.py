import fitz  # PyMuPDF
import re
import os
import sys

MAJOR_SECTION_NAMES = (
    r'Abstract|'
    r'Introduction|Background|Motivation|'
    r'Related\s+Work(?:s)?|Literature\s+Review|Prior\s+Work|'
    r'Method(?:ology)?|Materials?\s+and\s+Methods?|Methods?\s+and\s+Materials?|'
    r'Approach|Proposed\s+(?:Method|Approach|Framework|Model|System)|'
    r'System|Framework|Architecture|Model(?:\s+Design)?|'
    r'Experiment(?:s)?|Evaluation|Experimental\s+(?:Setup|Results)|'
    r'Result(?:s)?|Result(?:s)?\s+and\s+(?:Discussion|Analysis)|'
    r'Discussion|Analysis|'
    r'Conclusion(?:s)?|Conclusion(?:s)?\s+and\s+Future\s+Work|Future\s+Work|'
    r'Limitations?|'
    r'Acknowledgment(?:s)?|Acknowledgement(?:s)?|'
    r'Reference(?:s)?|Bibliography|Appendix'
)

MAJOR_HEADER_REGEX = re.compile(
    r'^\s*(?:[0-9]+\.?\s+|[IVXLCDM]+\.\s+)?(' + MAJOR_SECTION_NAMES + r')\s*[:.]?\s*$',
    re.IGNORECASE,
)
ABSTRACT_INLINE_REGEX = re.compile(r'^\s*Abstract\s*[—\-:]\s*', re.IGNORECASE)
ABSTRACT_ALONE_REGEX = re.compile(r'^\s*Abstract\s*[:.]?\s*$', re.IGNORECASE)

SUBSECTION_NUM_REGEX = re.compile(r'^\s*(\d+(?:\.\d+){1,3})\.?\s+([A-Z][^\n]{1,90})\s*$')
SUBSECTION_LETTER_REGEX = re.compile(r'^\s*([A-Z])\.\s+([A-Z][^\n]{1,90})\s*$')

PRUNE_KEYWORDS = ("references", "bibliography", "acknowledgment", "acknowledgements")
TABLE_CAPTION_REGEX = re.compile(r'\bTABLE\s+([IVXLCDM]+|\d+)\b', re.IGNORECASE)


def clean_text(text: str) -> str:
    """Cleans up white spaces, duplicate newlines, and ligatures."""
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', text)
    return text.strip()


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


def detect_pdf_layout(pdf_path: str, sample_pages: int = 6) -> str:
    """Classifies document as 'two_column' or 'single_column'."""
    doc = fitz.open(pdf_path)
    try:
        n_pages = len(doc)
        pages_to_check = list(range(1, min(n_pages, sample_pages + 1))) or [0]

        two_col_votes = 0
        single_col_votes = 0

        for page_num in pages_to_check:
            page = doc.load_page(page_num)
            page_width = page.rect.width
            mid_x = page_width / 2
            blocks = [b for b in page.get_text("blocks") if b[6] == 0 and b[4].strip()]
            if not blocks:
                continue

            spanning = left_only = right_only = 0
            for b in blocks:
                x0, x1 = b[0], b[2]
                if x0 < mid_x - 10 and x1 > mid_x + 10:
                    spanning += 1
                elif x1 <= mid_x + 10:
                    left_only += 1
                elif x0 >= mid_x - 10:
                    right_only += 1

            total = spanning + left_only + right_only
            if total == 0:
                continue

            if (left_only + right_only) / total > 0.55 and left_only > 0 and right_only > 0:
                two_col_votes += 1
            else:
                single_col_votes += 1

        return "two_column" if two_col_votes >= single_col_votes else "single_column"
    finally:
        doc.close()


def extract_blocks_two_column(page, full_width_ratio: float = 0.6) -> list:
    """Orders text blocks for a two-column page."""
    page_width = page.rect.width
    mid_x = page_width / 2
    raw_blocks = [b for b in page.get_text("blocks") if b[6] == 0 and b[4].strip()]
    raw_blocks.sort(key=lambda b: b[1])

    bands = []
    current_col_group = []
    for b in raw_blocks:
        width = b[2] - b[0]
        if width > full_width_ratio * page_width:
            if current_col_group:
                bands.append(('columns', current_col_group))
                current_col_group = []
            bands.append(('full', b))
        else:
            current_col_group.append(b)
    if current_col_group:
        bands.append(('columns', current_col_group))

    ordered = []
    for kind, payload in bands:
        if kind == 'full':
            ordered.append(payload)
        else:
            left = sorted([b for b in payload if (b[0] + b[2]) / 2 < mid_x], key=lambda b: b[1])
            right = sorted([b for b in payload if (b[0] + b[2]) / 2 >= mid_x], key=lambda b: b[1])
            ordered.extend(left)
            ordered.extend(right)
    return ordered


def extract_blocks_single_column(page) -> list:
    """Plain top-to-bottom reading order."""
    try:
        blocks = page.get_text("blocks", sort=True)
    except TypeError:
        blocks = page.get_text("blocks")
        blocks.sort(key=lambda b: (round(b[1], 1), b[0]))
    return [b for b in blocks if b[6] == 0 and b[4].strip()]


def _new_section_entry():
    return {"content": "", "subsections": {}}


def _flush_buffer(sections: dict, section: str, subsection: str, lines: list) -> None:
    if not lines:
        return
    text = clean_text("\n".join(lines))
    if not text:
        return
    if section not in sections:
        sections[section] = _new_section_entry()
    if subsection is None:
        existing = sections[section]["content"]
        sections[section]["content"] = (existing + "\n\n" + text) if existing else text
    else:
        subs = sections[section]["subsections"]
        subs[subsection] = (subs[subsection] + "\n\n" + text) if subsection in subs else text


def parse_pdf(pdf_path: str):
    """
    Parses a PDF file page-by-page, groups text into sections AND subsections,
    and prunes out bibliography/references/acknowledgments.
    """
    if not os.path.exists(pdf_path):
        return None

    layout = detect_pdf_layout(pdf_path)
    block_extractor = extract_blocks_two_column if layout == "two_column" else extract_blocks_single_column

    doc = fitz.open(pdf_path)

    sections = {}
    current_section = "Metadata / Front Matter"
    current_subsection = None
    buffer = []

    pruning_triggered = False
    abstract_extracted = False

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        blocks = block_extractor(page)

        for b in blocks:
            text = b[4].strip()
            if not text:
                continue

            lines = text.split('\n')
            first_line = lines[0]

            if not abstract_extracted and ABSTRACT_INLINE_REGEX.match(first_line):
                _flush_buffer(sections, current_section, current_subsection, buffer)
                buffer = []
                abstract_body = ABSTRACT_INLINE_REGEX.sub('', text, count=1)
                _flush_buffer(sections, "Abstract", None, [abstract_body])
                abstract_extracted = True
                continue

            major_title = _match_major_heading(first_line)
            sub_title = None
            if not major_title:
                sub_title = _match_subsection_heading(first_line)

            if major_title:
                header_lower = major_title.lower()

                if any(kw in header_lower for kw in PRUNE_KEYWORDS):
                    _flush_buffer(sections, current_section, current_subsection, buffer)
                    pruning_triggered = True
                    break

                _flush_buffer(sections, current_section, current_subsection, buffer)
                if ABSTRACT_ALONE_REGEX.match(major_title) and not abstract_extracted:
                    current_section = "Abstract"
                    abstract_extracted = True
                else:
                    current_section = major_title
                current_subsection = None
                buffer = lines[1:] if len(lines) > 1 else []

            elif sub_title:
                _flush_buffer(sections, current_section, current_subsection, buffer)
                current_subsection = sub_title
                buffer = lines[1:] if len(lines) > 1 else []

            else:
                buffer.append(text)

        if pruning_triggered:
            break

    if not pruning_triggered:
        _flush_buffer(sections, current_section, current_subsection, buffer)

    return sections
