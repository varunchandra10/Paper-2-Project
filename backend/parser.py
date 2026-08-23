# Facade for backward-compatibility with flat imports
from extraction.pymupdf_parser import (
    clean_text,
    detect_pdf_layout,
    extract_blocks_two_column,
    extract_blocks_single_column,
    extract_tables_for_page,
    parse_pdf
)