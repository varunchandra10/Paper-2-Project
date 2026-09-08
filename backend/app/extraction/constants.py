"""
Centralized Extraction Header Regexes and Pruning Rules.
Decouples PyMuPDF parser and section detector.
"""
import re

MAJOR_SECTION_NAMES = (
    r'Abstract|'
    r'Introduction|Background|Motivation|'
    r'Related[-\s]Work(?:s)?|Literature\s+Review|Prior\s+Work|'
    r'Method(?:ology)?|Materials?\s+and\s+Methods?|Methods?\s+and\s+Materials?|'
    r'Approach|Proposed\s+(?:Method|Approach|Framework|Model|System|Architecture)|'
    r'System|Framework|Architecture|Model(?:\s+Design)?|'
    r'Experiment(?:s)?|Evaluation|Experimental\s+(?:Setup|Results|Evaluation)|'
    r'Result(?:s)?|Result(?:s)?\s+and\s+(?:Discussion|Analysis)|'
    r'Discussion|Analysis|'
    r'Conclusion(?:s)?|Conclusion(?:s)?\s+and\s+Future\s+Work|Future\s+Work|'
    r'Limitations?|'
    r'Acknowledgment(?:s)?|Acknowledgement(?:s)?|'
    r'Reference(?:s)?|Bibliography|Appendix'
)

# Matches standard major section headers (numbered or unnumbered)
MAJOR_HEADER_REGEX = re.compile(
    r'^\s*(?:[0-9]+(?:\.[0-9]+)*\.?\s+|[IVXLCDM]+(?:\.[0-9]+)*[\.\s\-–—]+)?(' + MAJOR_SECTION_NAMES + r')\s*[:.]?\s*$',
    re.IGNORECASE,
)

# Matches Roman numeral headers with arbitrary titles (e.g. III. PROPOSED ARCHITECTURE, IV. EXPERIMENTS)
ROMAN_NUMERAL_HEADER_REGEX = re.compile(
    r'^\s*([IVXLCDM]+(?:-[A-Z])?)(?:[\.\s\-–—]+|\s+)([A-Z][A-Za-z0-9\s\-_–—:]{2,90})\s*$'
)

# Matches Arabic numbered headers with arbitrary titles and hyphens (e.g. 1. OVERVIEW, 2. SYSTEM-ARCHITECTURE)
NUMBERED_HEADER_REGEX = re.compile(
    r'^\s*(\d+(?:\.\d+)*)(?:[\.\s\-–—]+|\s+)([A-Z][A-Za-z0-9\s\-_–—:]{2,90})\s*$'
)

ABSTRACT_INLINE_REGEX = re.compile(r'^\s*Abstract\s*[—\-:]\s*', re.IGNORECASE)
ABSTRACT_ALONE_REGEX = re.compile(r'^\s*Abstract\s*[:.]?\s*$', re.IGNORECASE)

SUBSECTION_NUM_REGEX = re.compile(r'^\s*(\d+(?:\.\d+){1,3})\.?\s+([A-Z][^\n]{1,90})\s*$')
SUBSECTION_LETTER_REGEX = re.compile(r'^\s*([A-Z])\.\s+([A-Z][^\n]{1,90})\s*$')

PRUNE_KEYWORDS = ("references", "bibliography", "acknowledgment", "acknowledgements")
TABLE_CAPTION_REGEX = re.compile(r'\bTABLE\s+([IVXLCDM]+|\d+)\b', re.IGNORECASE)
