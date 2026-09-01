import os
import re
import fitz  # PyMuPDF


def get_paper_slug_id(filename: str) -> str:
    """Generates canonical paper_id matching original backend schema."""
    base_name = os.path.splitext(filename)[0]
    clean_title = re.sub(r'[^a-z0-9\s]', '', base_name.lower()).strip()
    slug = re.sub(r'\s+', '_', clean_title)[:30].strip('_')
    return f"paper_{slug}" if slug else "paper_document"


def inspect_pdf(pdf_path: str) -> dict:
    """
    Inspects a scientific PDF file using PyMuPDF to validate layout,
    detect pages, text presence, scanned content, and encryption status.
    """
    filename = os.path.basename(pdf_path)
    paper_id = get_paper_slug_id(filename)
    
    report = {
        "paper_id": paper_id,
        "filename": filename,
        "valid": False,
        "pages": 0,
        "has_text": False,
        "has_images": False,
        "is_scanned": False,
        "needs_ocr": False,
        "is_encrypted": False,
        "text_coverage_chars": 0,
        "suspicious_empty_pages": [],
        "error_message": None
    }
    
    if not os.path.exists(pdf_path):
        report["error_message"] = f"File not found at path: {pdf_path}"
        return report

    doc = None
    try:
        doc = fitz.open(pdf_path)
        report["valid"] = True
        report["pages"] = len(doc)
        report["is_encrypted"] = doc.is_encrypted
        
        total_text_len = 0
        has_images = False
        empty_pages = []
        
        for idx in range(len(doc)):
            page = doc.load_page(idx)
            page_num = idx + 1
            
            # Detect text on page
            page_text = page.get_text("text").strip()
            page_text_len = len(page_text)
            total_text_len += page_text_len
            
            if page_text_len == 0:
                empty_pages.append(page_num)
                
            # Detect image objects
            if not has_images and len(page.get_images()) > 0:
                has_images = True
                
        report["text_coverage_chars"] = total_text_len
        report["has_text"] = total_text_len > 0
        report["has_images"] = has_images
        report["suspicious_empty_pages"] = empty_pages
        
        avg_chars_per_page = total_text_len / len(doc) if len(doc) > 0 else 0
        if total_text_len == 0 or avg_chars_per_page < 100:
            report["is_scanned"] = True
            report["needs_ocr"] = True
            
    except Exception as e:
        report["valid"] = False
        report["error_message"] = str(e)
    finally:
        if doc:
            doc.close()
            
    return report
