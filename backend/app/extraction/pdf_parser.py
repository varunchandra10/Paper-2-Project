"""
Adaptive Document Extraction Pipeline Entry Point.

Executes deterministic-first document routing, targeted visual element transcription,
consensus merging, element-level quality validation, and separate semantic conceptual analysis.
"""

import os
import re
from typing import List, Dict, Any
from app.extraction.router import route_and_extract
from app.extraction.merger import merge_extractions
from app.extraction.validator import validate_paper_document
from app.extraction.semantic_analyzer import SemanticResearchAnalyzer
from app.schemas.canonical_paper import PaperDocument


def parse_pdf_document(pdf_path: str) -> PaperDocument:
    """
    Executes the complete adaptive deterministic-first extraction pipeline.
    """
    filename = os.path.basename(pdf_path)

    # 1. Multi-signal deterministic extraction & targeted VLM routing
    routed_data = route_and_extract(pdf_path)

    # 2. Canonical consensus merger with provenance tracking
    paper_doc = merge_extractions(routed_data)

    # 3. Element-level quality validation scorecard
    quality_report = validate_paper_document(paper_doc)
    paper_doc.extraction_metadata["quality_report"] = quality_report.model_dump()
    paper_doc.extraction_metadata["element_confidence"] = quality_report.element_confidence

    # 4. Separate Semantic Conceptual Understanding (Methodology, Contributions, Limitations)
    try:
        analyzer = SemanticResearchAnalyzer()
        semantics = analyzer.analyze_document_semantics(paper_doc)
        paper_doc.extraction_metadata["semantic_analysis"] = semantics
    except Exception as sem_err:
        print(f"[PARSER WARN] Semantic analysis notice: {sem_err}")
        paper_doc.extraction_metadata["semantic_analysis"] = {}

    return paper_doc
