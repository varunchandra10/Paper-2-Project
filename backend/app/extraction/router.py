"""
Adaptive Deterministic-First Document Extraction Router.

Follows the strict production hierarchy:
1. Inspects & deduplicates PDF.
2. Extracts document blocks & reading-order hierarchy deterministically via PyMuPDF (0 tokens).
3. Detects complex visual elements (Figures, Tables, Equations).
4. Evaluates whether local deterministic parsing is sufficient.
5. Dispatches targeted VLM crops ONLY when visual interpretation is actually required and quota is available.
6. Implements seamless local fallback when quota is exhausted.
"""

import os
import time
import requests
from typing import List, Dict, Any, Optional
from app.extraction.pdf_inspector import inspect_pdf
from app.extraction.block_extractor import extract_document_blocks
from app.extraction.section_detector import detect_sections
from app.extraction.element_cropper import ElementCropper, ElementCandidate
from app.extraction.vlm_processor import VLMElementProcessor
from app.extraction.grobid_parser import extract_grobid
from app.extraction.docling_parser import extract_docling
from app.core.quota_tracker import daily_quota_manager


def route_and_extract(pdf_path: str, grobid_url: str = "http://localhost:8070") -> dict:
    """
    Executes the adaptive deterministic-first extraction pipeline.
    """
    t_start = time.time()
    filename = os.path.basename(pdf_path)

    # ── 1. PDF Inspector Diagnostics ──
    t_inspect_start = time.time()
    inspector_report = inspect_pdf(pdf_path)
    t_inspect_ms = round((time.time() - t_inspect_start) * 1000, 2)

    result = {
        "paper_id": inspector_report["paper_id"],
        "filename": inspector_report["filename"],
        "inspector_report": inspector_report,
        "selected_parsers": [],
        "pymupdf_output": None,
        "docling_output": None,
        "vlm_elements": {"figures": [], "tables": [], "equations": []},
        "grobid_output": None,
        "element_candidates": {"figures": [], "tables": [], "equations": []},
        "timing_metrics": {},
        "vlm_usage": {"used_vlm": False, "requests": 0, "input_tokens": 0, "output_tokens": 0},
        "valid": inspector_report["valid"],
        "error_message": inspector_report["error_message"]
    }

    if not inspector_report["valid"]:
        return result

    # ── 2. Handle Scanned PDFs (Docling OCR Route) ──
    if inspector_report["is_scanned"]:
        result["selected_parsers"].append("docling")
        docling_out = extract_docling(pdf_path)
        result["docling_output"] = docling_out
        result["valid"] = docling_out.get("valid", False)
        result["error_message"] = docling_out.get("error_message")
        result["timing_metrics"]["total_time_ms"] = round((time.time() - t_start) * 1000, 2)
        return result

    # ── 3. Deterministic Extraction (PyMuPDF Layout & Reading Order) ──
    t_det_start = time.time()
    result["selected_parsers"].append("pymupdf")
    raw_full_text = ""
    try:
        blocks = extract_document_blocks(pdf_path)
        sections = detect_sections(blocks)
        result["pymupdf_output"] = sections

        text_parts = []
        for p in blocks:
            for b in p.get("blocks", []):
                t = b.get("text", "").strip()
                if t:
                    text_parts.append(t)
        raw_full_text = "\n\n".join(text_parts)
    except Exception as py_err:
        print(f"[ROUTER WARN] PyMuPDF deterministic extraction warning: {py_err}")

    t_det_ms = round((time.time() - t_det_start) * 1000, 2)

    # ── 4. Complex Visual Element Detection & Cropping ──
    t_crop_start = time.time()
    cropper = ElementCropper(paper_id=result["paper_id"])
    detected = cropper.detect_and_crop_elements(pdf_path)
    result["element_candidates"] = {
        "figures": [c.to_dict() for c in detected.get("figures", [])],
        "tables": [c.to_dict() for c in detected.get("tables", [])],
        "equations": [c.to_dict() for c in detected.get("equations", [])]
    }
    t_crop_ms = round((time.time() - t_crop_start) * 1000, 2)

    # Evaluate whether VLM is required for any complex element
    figures_needing_vlm = [f for f in detected.get("figures", []) if f.needs_vlm]
    tables_needing_vlm = [t for t in detected.get("tables", []) if t.needs_vlm]
    equations_needing_vlm = [e for e in detected.get("equations", []) if e.needs_vlm]

    total_elements_needing_vlm = len(figures_needing_vlm) + len(tables_needing_vlm) + len(equations_needing_vlm)
    is_vlm_required = total_elements_needing_vlm > 0

    # ── 5. Targeted VLM Execution (or Local Quota Fallback) ──
    t_vlm_start = time.time()
    quota_available = daily_quota_manager.can_use_vlm()
    vlm_retry_count = 0
    vlm_req_count = 0
    total_in_tok = 0
    total_out_tok = 0

    if is_vlm_required and quota_available:
        result["selected_parsers"].append("gemini_vlm")
        vlm = VLMElementProcessor()

        # Targeted Figure Processing
        for fig in figures_needing_vlm[:6]:  # Cap per paper budget
            if fig.image_path and os.path.exists(fig.image_path):
                fig_res = vlm.process_figure(fig.element_id, fig.image_path, fig.caption)
                vlm_req_count += 1
                tok = fig_res.get("tokens_used", 300)
                in_tok = int(tok * 0.7)
                out_tok = int(tok * 0.3)
                total_in_tok += in_tok
                total_out_tok += out_tok
                daily_quota_manager.record_vlm_request(result["paper_id"], "figure", in_tok, out_tok)
                result["vlm_elements"]["figures"].append(fig_res)

        # Targeted Complex Table Processing with Self-Healing Retry
        for tab in tables_needing_vlm[:6]:
            if tab.image_path and os.path.exists(tab.image_path):
                tab_res = vlm.process_table(tab.element_id, tab.image_path, tab.caption, tab.content_text)
                vlm_req_count += 1
                tok = tab_res.get("tokens_used", 350)
                in_tok = int(tok * 0.7)
                out_tok = int(tok * 0.3)
                total_in_tok += in_tok
                total_out_tok += out_tok
                daily_quota_manager.record_vlm_request(result["paper_id"], "table", in_tok, out_tok)

                # Self-Healing Check: If markdown table missing columns/pipes, retry once at 250 DPI
                md = tab_res.get("content_markdown", "")
                if "|" not in md or len(tab_res.get("rows", [])) == 0:
                    try:
                        hq_crop_path = cropper.re_crop_element(pdf_path, tab, elevated_dpi=250)
                        if hq_crop_path and os.path.exists(hq_crop_path):
                            vlm_retry_count += 1
                            tab_res_retry = vlm.process_table(tab.element_id, hq_crop_path, tab.caption, tab.content_text)
                            r_tok = tab_res_retry.get("tokens_used", 350)
                            total_in_tok += int(r_tok * 0.7)
                            total_out_tok += int(r_tok * 0.3)
                            daily_quota_manager.record_vlm_request(result["paper_id"], "table_retry", int(r_tok * 0.7), int(r_tok * 0.3))
                            if "|" in tab_res_retry.get("content_markdown", ""):
                                tab_res = tab_res_retry
                    except Exception as heal_err:
                        print(f"[ROUTER WARN] Table self-healing notice: {heal_err}")

                result["vlm_elements"]["tables"].append(tab_res)

        # Targeted Complex Equation Processing with Self-Healing Retry
        for eq in equations_needing_vlm[:8]:
            if eq.image_path and os.path.exists(eq.image_path):
                eq_res = vlm.process_equation(eq.element_id, eq.image_path, eq.caption, eq.content_text)
                vlm_req_count += 1
                tok = eq_res.get("tokens_used", 250)
                in_tok = int(tok * 0.7)
                out_tok = int(tok * 0.3)
                total_in_tok += in_tok
                total_out_tok += out_tok
                daily_quota_manager.record_vlm_request(result["paper_id"], "equation", in_tok, out_tok)

                # Self-Healing Check: If unbalanced LaTeX braces or empty formula, retry once at 250 DPI
                latex = eq_res.get("latex", "")
                if latex.count("{") != latex.count("}") or len(latex.strip()) < 2:
                    try:
                        hq_crop_path = cropper.re_crop_element(pdf_path, eq, elevated_dpi=250)
                        if hq_crop_path and os.path.exists(hq_crop_path):
                            vlm_retry_count += 1
                            eq_res_retry = vlm.process_equation(eq.element_id, hq_crop_path, eq.caption, eq.content_text)
                            r_tok = eq_res_retry.get("tokens_used", 250)
                            total_in_tok += int(r_tok * 0.7)
                            total_out_tok += int(r_tok * 0.3)
                            daily_quota_manager.record_vlm_request(result["paper_id"], "equation_retry", int(r_tok * 0.7), int(r_tok * 0.3))
                            if eq_res_retry.get("latex", "").count("{") == eq_res_retry.get("latex", "").count("}"):
                                eq_res = eq_res_retry
                    except Exception as heal_err:
                        print(f"[ROUTER WARN] Equation self-healing notice: {heal_err}")

                result["vlm_elements"]["equations"].append(eq_res)

        result["vlm_usage"] = {
            "used_vlm": True,
            "requests": vlm_req_count,
            "vlm_retry_count": vlm_retry_count,
            "input_tokens": total_in_tok,
            "output_tokens": total_out_tok,
            "total_tokens": total_in_tok + total_out_tok,
            "token_usage_available": bool(total_in_tok > 0),
            "quota_consumed": True,
            "fallback_reason": None
        }
        daily_quota_manager.record_paper_completion(result["paper_id"], used_vlm=True)
        print(f"[ROUTER] Completed targeted VLM processing for '{result['paper_id']}' ({vlm_req_count} elements, {vlm_retry_count} retries, {total_in_tok + total_out_tok} tokens).")

    else:
        # 100% Local Processing Mode (No VLM called or Quota Exhausted)
        status_reason = "pure_deterministic_document" if not is_vlm_required else "daily_quota_exhausted"
        result["vlm_usage"] = {
            "used_vlm": False,
            "requests": 0,
            "vlm_retry_count": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "token_usage_available": True,
            "quota_consumed": False,
            "status": "skipped",
            "reason": status_reason,
            "fallback_reason": status_reason
        }
        daily_quota_manager.record_paper_completion(result["paper_id"], used_vlm=False)
        print(f"[ROUTER] Processed '{result['paper_id']}' with 100% local deterministic pipeline (reason: {status_reason}).")

    t_vlm_ms = round((time.time() - t_vlm_start) * 1000, 2)
    t_local_ms = round(t_inspect_ms + t_det_ms + t_crop_ms, 2)

    # ── 6. Standby Parsers (GROBID / Docling for supplementary citations/tables) ──
    grobid_alive = False
    try:
        r = requests.get(f"{grobid_url.rstrip('/')}/api/isalive", timeout=1.0)
        if r.status_code == 200 and r.text.strip() == "true":
            grobid_alive = True
    except Exception:
        pass

    if grobid_alive:
        try:
            grobid_out = extract_grobid(pdf_path, grobid_url=grobid_url)
            if grobid_out.get("valid"):
                result["grobid_output"] = grobid_out
                result["selected_parsers"].append("grobid")
        except Exception as gr_err:
            print(f"[ROUTER WARN] GROBID standby parsing notice: {gr_err}")

    # ── 7. Performance & Complete Timing Metrics ──
    t_total_ms = round((time.time() - t_start) * 1000, 2)
    result["timing_metrics"] = {
        "inspection_time_ms": t_inspect_ms,
        "deterministic_time_ms": t_det_ms,
        "element_detection_time_ms": t_crop_ms,
        "vlm_time_ms": t_vlm_ms,
        "local_processing_latency_ms": t_local_ms,
        "total_pipeline_latency_ms": t_total_ms,
        "total_time_ms": t_total_ms
    }

    # Record complete execution instrumentation for benchmark and auditing
    result["instrumentation"] = {
        "paper_id": result["paper_id"],
        "total_pages": inspector_report.get("pages", 1),
        "elements_detected": {
            "figures_detected": len(detected.get("figures", [])),
            "tables_detected": len(detected.get("tables", [])),
            "equations_detected": len(detected.get("equations", []))
        },
        "elements_sent_to_vlm": total_elements_needing_vlm if (is_vlm_required and quota_available) else 0,
        "vlm_request_count": vlm_req_count,
        "vlm_retry_count": vlm_retry_count,
        "input_tokens": total_in_tok,
        "output_tokens": total_out_tok,
        "total_tokens": total_in_tok + total_out_tok,
        "token_usage_available": bool(total_in_tok > 0 or not is_vlm_required),
        "vlm_latency_ms": t_vlm_ms,
        "local_processing_latency_ms": t_local_ms,
        "total_pipeline_latency_ms": t_total_ms,
        "quota_consumed": bool(is_vlm_required and quota_available),
        "fallback_reason": result["vlm_usage"].get("fallback_reason")
    }

    result["valid"] = bool(result["pymupdf_output"] or result["docling_output"])

    return result

