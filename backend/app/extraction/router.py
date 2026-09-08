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
        "docling_output": None,
        "gemini_output": None,
        "grobid_output": None,
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

    # --- STREAM 1: LOCAL FULL EXTRACTION (PyMuPDF + Docling) ---
    
    # 3. PyMuPDF: Base Layout & Full Text Blocks
    result["selected_parsers"].append("pymupdf")
    raw_full_text = ""
    try:
        blocks = extract_document_blocks(pdf_path)
        sections = detect_sections(blocks)
        result["pymupdf_output"] = sections
        
        # Compile complete text stream across all blocks
        text_parts = []
        for p in blocks:
            for b in p.get("blocks", []):
                t = b.get("text", "").strip()
                if t:
                    text_parts.append(t)
        raw_full_text = "\n\n".join(text_parts)
    except Exception as py_err:
        print(f"[ROUTER WARN] PyMuPDF parser node warning: {py_err}")

    # 4. Docling: Visual Markdown Tables & Structure
    try:
        print(f"[ROUTER] Running Docling for visual Markdown table extraction...")
        docling_out = extract_docling(pdf_path)
        if docling_out.get("valid"):
            result["docling_output"] = docling_out
            result["selected_parsers"].append("docling")
    except Exception as doc_err:
        print(f"[ROUTER WARN] Docling extraction warning: {doc_err}")

    # --- GROBID ON STANDBY (ONLY IF USER HAS IT ACTIVE) ---
    grobid_alive = False
    try:
        r = requests.get(f"{grobid_url.rstrip('/')}/api/isalive", timeout=1.5)
        if r.status_code == 200 and r.text.strip() == "true":
            grobid_alive = True
    except Exception:
        pass

    if grobid_alive:
        try:
            print(f"[ROUTER] GROBID detected on standby ({grobid_url}). Collecting TEI citations...")
            grobid_out = extract_grobid(pdf_path, grobid_url=grobid_url)
            if grobid_out.get("valid"):
                result["grobid_output"] = grobid_out
                result["selected_parsers"].append("grobid")
        except Exception as gr_err:
            print(f"[ROUTER WARN] GROBID standby parsing notice: {gr_err}")

    # --- STREAM 2: GOOGLE GEMINI FULL EXTRACTION (PRIMARY WEIGHTAGE) ---
    try:
        from app.extraction.openrouter_parser import extract_full_document_gemini
        # Feed complete paper text stream to Gemini 2.0 Flash
        text_for_gemini = raw_full_text
        if not text_for_gemini and result["pymupdf_output"]:
            # Fallback to section content concatenation
            sec_texts = []
            for s_name, s_val in result["pymupdf_output"].get("sections", {}).items():
                sec_texts.append(f"## {s_name}\n" + s_val.get("content", ""))
            text_for_gemini = "\n\n".join(sec_texts)

        if text_for_gemini:
            print(f"[ROUTER] Triggering Google Gemini 2.0 Flash full-document extraction...")
            gemini_out = extract_full_document_gemini(text_for_gemini, paper_id=result["paper_id"])
            if gemini_out.get("valid"):
                result["gemini_output"] = gemini_out
                result["selected_parsers"].append("gemini")
                print(f"[ROUTER SUCCESS] Google Gemini full extraction succeeded with primary weightage.")
    except Exception as gem_err:
        print(f"[ROUTER WARN] Google Gemini extraction notice: {gem_err}")

    result["valid"] = bool(result["gemini_output"] or result["pymupdf_output"] or result["docling_output"])

    # =========================================================================
    # [LEGACY ROUTER CODE - PRESERVED & COMMENTED OUT AS PER INSTRUCTION]
    # Previously, GROBID was tried first, then fell back to Docling for all content:
    #
    # grobid_alive = False
    # try:
    #     r = requests.get(f"{grobid_url.rstrip('/')}/api/isalive", timeout=3)
    #     if r.status_code == 200 and r.text.strip() == "true":
    #         grobid_alive = True
    # except Exception:
    #     pass
    #
    # if grobid_alive:
    #     result["selected_parsers"].append("grobid")
    #     grobid_out = extract_grobid(pdf_path, grobid_url=grobid_url)
    #     if grobid_out.get("valid"):
    #         result["grobid_output"] = grobid_out
    #     else:
    #         result["selected_parsers"].append("docling")
    #         docling_out = extract_docling(pdf_path)
    #         result["docling_output"] = docling_out
    # else:
    #     result["selected_parsers"].append("docling")
    #     docling_out = extract_docling(pdf_path)
    #     result["docling_output"] = docling_out
    #
    # py_tables = result["pymupdf_output"].get("sections", {}).get("Tables", {}).get("subsections", {}) if result["pymupdf_output"] else {}
    # gr_tables = result["grobid_output"].get("tables", []) if result["grobid_output"] else []
    # if len(py_tables) == 0 and len(gr_tables) == 0 and "docling" not in result["selected_parsers"]:
    #     ...
    # =========================================================================

    return result
