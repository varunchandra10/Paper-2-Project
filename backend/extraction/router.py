import os
import requests
from typing import List, Dict, Any
from core import logger, generate_paper_id
from extraction.pdf_inspector import inspect_pdf
from extraction.block_extractor import extract_document_blocks
from extraction.section_detector import detect_sections
from extraction.grobid_parser import extract_grobid
from extraction.docling_parser import extract_docling


def route_and_extract(pdf_path: str, grobid_url: str = "http://localhost:8070") -> dict:
    """
    Analyzes the target PDF file using the pdf_inspector, and dynamically
    routes extraction through PyMuPDF, GROBID, and/or Docling.
    Implements failover rules to Docling if GROBID is unresponsive.
    """
    filename = os.path.basename(pdf_path)
    logger.info(f"🚀 Starting routed extraction pipeline for '{filename}'...")
    
    # 1. Run PDF Inspector diagnostics
    inspector_report = inspect_pdf(pdf_path)
    
    result = {
        "paper_id": inspector_report["paper_id"],
        "filename": inspector_report["filename"],
        "inspector_report": inspector_report,
        "selected_parsers": [],
        "pymupdf_output": None,
        "grobid_output": None,
        "docling_output": None,
        "valid": inspector_report["valid"],
        "error_message": inspector_report["error_message"]
    }
    
    if not inspector_report["valid"]:
        logger.error(f"Aborting extraction. Invalid PDF '{filename}': {inspector_report['error_message']}")
        return result

    # 2. Check if the PDF is scanned (requires OCR layout processing)
    if inspector_report["is_scanned"]:
        logger.info(f"PDF '{filename}' is classified as SCANNED. Routing to Docling OCR engine.")
        result["selected_parsers"].append("docling")
        docling_out = extract_docling(pdf_path)
        result["docling_output"] = docling_out
        result["valid"] = docling_out.get("valid", False)
        result["error_message"] = docling_out.get("error_message")
        return result

    # 3. Digital PDF Path: Run PyMuPDF as the base layout parser
    logger.info(f"Routing '{filename}' to PyMuPDF text & section parser.")
    result["selected_parsers"].append("pymupdf")
    try:
        blocks = extract_document_blocks(pdf_path)
        sections = detect_sections(blocks)
        result["pymupdf_output"] = sections
    except Exception as py_err:
        logger.error(f"PyMuPDF parser node failed: {py_err}")

    # 4. Attempt GROBID extraction with Docling failover
    logger.info(f"Checking GROBID server availability at {grobid_url}...")
    grobid_alive = False
    try:
        # Ping check
        r = requests.get(f"{grobid_url.rstrip('/')}/api/isalive", timeout=3)
        if r.status_code == 200 and r.text.strip() == "true":
            grobid_alive = True
    except Exception:
        pass

    if grobid_alive:
        logger.info(f"GROBID is active. Routing '{filename}' to GROBID.")
        result["selected_parsers"].append("grobid")
        grobid_out = extract_grobid(pdf_path, grobid_url=grobid_url)
        
        if grobid_out.get("valid"):
            result["grobid_output"] = grobid_out
        else:
            logger.warning("GROBID parser failed. Engaging failover to Docling.")
            result["selected_parsers"].append("docling")
            docling_out = extract_docling(pdf_path)
            result["docling_output"] = docling_out
    else:
        logger.warning(f"GROBID is offline at {grobid_url}. Engaging failover to Docling for '{filename}'.")
        result["selected_parsers"].append("docling")
        docling_out = extract_docling(pdf_path)
        result["docling_output"] = docling_out

    logger.info(f"🏁 Finished routed extraction for '{filename}'. Selected: {result['selected_parsers']}")
    return result
