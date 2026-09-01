import os
import re
import requests
from typing import List, Dict, Any
from app.extraction.pdf_inspector import inspect_pdf
from app.extraction.block_extractor import extract_document_blocks
from app.extraction.section_detector import detect_sections
from app.extraction.grobid_parser import extract_grobid
from app.extraction.docling_parser import extract_docling


def route_and_extract(pdf_path: str, grobid_url: str = "http://localhost:8070") -> dict:
    """
    Analyzes the target PDF file using pdf_inspector, and dynamically
    routes extraction through PyMuPDF, GROBID, and/or Docling.
    Implements failover rules to Docling if GROBID is unresponsive.
    """
    filename = os.path.basename(pdf_path)
    
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
        return result

    # 2. Check if PDF is scanned
    if inspector_report["is_scanned"]:
        result["selected_parsers"].append("docling")
        docling_out = extract_docling(pdf_path)
        result["docling_output"] = docling_out
        result["valid"] = docling_out.get("valid", False)
        result["error_message"] = docling_out.get("error_message")
        return result

    # 3. Digital PDF Path: Run PyMuPDF as base layout parser
    result["selected_parsers"].append("pymupdf")
    try:
        blocks = extract_document_blocks(pdf_path)
        sections = detect_sections(blocks)
        result["pymupdf_output"] = sections
    except Exception as py_err:
        print(f"[ROUTER WARN] PyMuPDF parser node warning: {py_err}")

    # 4. Attempt GROBID extraction with Docling failover
    grobid_alive = False
    try:
        r = requests.get(f"{grobid_url.rstrip('/')}/api/isalive", timeout=3)
        if r.status_code == 200 and r.text.strip() == "true":
            grobid_alive = True
    except Exception:
        pass

    if grobid_alive:
        result["selected_parsers"].append("grobid")
        grobid_out = extract_grobid(pdf_path, grobid_url=grobid_url)
        if grobid_out.get("valid"):
            result["grobid_output"] = grobid_out
        else:
            result["selected_parsers"].append("docling")
            docling_out = extract_docling(pdf_path)
            result["docling_output"] = docling_out
    else:
        result["selected_parsers"].append("docling")
        docling_out = extract_docling(pdf_path)
        result["docling_output"] = docling_out

    # 5. Auxiliary Table Routing
    py_tables = result["pymupdf_output"].get("sections", {}).get("Tables", {}).get("subsections", {}) if result["pymupdf_output"] else {}
    gr_tables = result["grobid_output"].get("tables", []) if result["grobid_output"] else []
    
    if len(py_tables) == 0 and len(gr_tables) == 0 and "docling" not in result["selected_parsers"]:
        text_content = ""
        if result["pymupdf_output"]:
            for sec_name, sec_data in result["pymupdf_output"].get("sections", {}).items():
                text_content += sec_data.get("content", "") + " "
                for sub_text in sec_data.get("subsections", {}).values():
                    text_content += sub_text + " "
        if result["grobid_output"]:
            text_content += result["grobid_output"].get("abstract", "") + " "
            for sec_name, sec_data in result["grobid_output"].get("sections", {}).items():
                text_content += sec_data.get("content", "") + " "
                for sub_text in sec_data.get("subsections", {}).values():
                    text_content += sub_text + " "
                    
        table_mentions = re.findall(r'\b(?:Table|TABLE)\s*(?:[IVX\d]+)\b', text_content)
        if table_mentions:
            result["selected_parsers"].append("docling")
            docling_out = extract_docling(pdf_path)
            result["docling_output"] = docling_out

    return result
