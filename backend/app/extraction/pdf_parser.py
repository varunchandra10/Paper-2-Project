import os
import re
from typing import List, Dict, Any
from app.extraction.router import route_and_extract
from app.extraction.merger import merge_extractions
from app.extraction.validator import validate_paper_document
from app.schemas.canonical_paper import PaperDocument, Section


def parse_pdf_document(pdf_path: str) -> PaperDocument:
    """
    Seamlessly routes, merges, and validates scientific PDF papers
    using PyMuPDF, Grobid TEI-XML, and Docling multi-parser consensus.
    """
    filename = os.path.basename(pdf_path)
    
    # 1. Multi-parser routing
    routed_data = route_and_extract(pdf_path)
    
    # 2. Consensus merger
    paper_doc = merge_extractions(routed_data)
    
    # 3. Validation scorecard
    quality_report = validate_paper_document(paper_doc)
    paper_doc.extraction_metadata["quality_report"] = quality_report.model_dump()
    
    return paper_doc
