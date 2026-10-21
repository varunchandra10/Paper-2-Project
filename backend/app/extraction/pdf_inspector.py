import os
import re
import pymupdf as fitz
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class DocumentComplexityProfile(BaseModel):
    """Structured complexity profile for an academic document."""
    scanned_page_ratio: float = Field(default=0.0, description="Ratio of scanned/image-only pages to total pages")
    multi_column_detected: bool = Field(default=False, description="Whether multi-column layout was detected")
    figure_count: int = Field(default=0, description="Number of detected visual figures/images")
    table_count: int = Field(default=0, description="Number of detected tabular blocks")
    equation_count: int = Field(default=0, description="Number of detected math equation blocks")
    vector_graphics_count: int = Field(default=0, description="Total vector graphic path objects detected")
    reading_order_conflicts: int = Field(default=0, description="Number of detected reading order out-of-sequence jumps")
    extraction_confidence: float = Field(default=1.0, description="Baseline deterministic extraction confidence (0.0 to 1.0)")
    visual_density: float = Field(default=0.0, description="Visual graphic density ratio (graphics per page)")
    complexity_level: str = Field(default="LOW", description="Overall complexity class: 'LOW', 'MEDIUM', 'HIGH'")


def get_paper_slug_id(filename: str) -> str:
    """Generates canonical paper_id matching original backend schema."""
    base_name = os.path.splitext(filename)[0]
    clean_title = re.sub(r'[^a-z0-9\s]', '', base_name.lower()).strip()
    slug = re.sub(r'\s+', '_', clean_title)[:30].strip('_')
    return f"paper_{slug}" if slug else "paper_document"


def inspect_pdf(pdf_path: str) -> dict:
    """
    Inspects a scientific PDF file using PyMuPDF to validate layout,
    detect pages, text presence, scanned content, column layouts, vector graphics,
    and constructs a structured DocumentComplexityProfile.
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
        "complexity_profile": DocumentComplexityProfile().model_dump(),
        "error_message": None
    }

    if not os.path.exists(pdf_path):
        report["error_message"] = f"File not found at path: {pdf_path}"
        return report

    doc = None
    try:
        doc = fitz.open(pdf_path)
        total_pages = len(doc)
        report["valid"] = True
        report["pages"] = total_pages
        report["is_encrypted"] = doc.is_encrypted

        total_text_len = 0
        has_images = False
        empty_pages = []
        scanned_pages_count = 0
        total_drawings = 0
        total_images_count = 0
        multi_col_votes = 0

        for idx in range(total_pages):
            page = doc.load_page(idx)
            page_num = idx + 1

            # Detect text and blocks
            blocks = page.get_text("blocks")
            page_text = "".join([b[4] for b in blocks if b[6] == 0]).strip()
            page_text_len = len(page_text)
            total_text_len += page_text_len

            if page_text_len == 0:
                empty_pages.append(page_num)
                scanned_pages_count += 1
            elif page_text_len < 100:
                scanned_pages_count += 1

            # Detect image objects
            img_list = page.get_images()
            total_images_count += len(img_list)
            if len(img_list) > 0:
                has_images = True

            # Detect vector graphics / drawings
            try:
                drawings = page.get_drawings()
                total_drawings += len(drawings)
            except Exception:
                pass

            # Detect multi-column layout by inspecting horizontal block distributions
            text_blocks = [b for b in blocks if b[6] == 0 and len(b[4].strip()) > 30]
            if len(text_blocks) >= 4:
                col_left = sum(1 for b in text_blocks if b[0] < page.rect.width * 0.45)
                col_right = sum(1 for b in text_blocks if b[0] > page.rect.width * 0.45)
                if col_left >= 2 and col_right >= 2:
                    multi_col_votes += 1

        report["text_coverage_chars"] = total_text_len
        report["has_text"] = total_text_len > 0
        report["has_images"] = has_images
        report["suspicious_empty_pages"] = empty_pages

        avg_chars_per_page = total_text_len / total_pages if total_pages > 0 else 0
        is_scanned = (total_text_len == 0 or avg_chars_per_page < 100 or (scanned_pages_count / total_pages > 0.6 if total_pages else False))
        report["is_scanned"] = is_scanned
        report["needs_ocr"] = is_scanned

        # Construct DocumentComplexityProfile
        scanned_ratio = round(scanned_pages_count / total_pages, 2) if total_pages > 0 else 0.0
        multi_col_detected = (multi_col_votes / total_pages > 0.3) if total_pages > 0 else False
        visual_density = round((total_images_count + (total_drawings / 10.0)) / max(1, total_pages), 2)

        # Baseline extraction confidence based on text coverage
        if is_scanned:
            det_conf = 0.30
        elif avg_chars_per_page > 1000:
            det_conf = 0.98
        elif avg_chars_per_page > 500:
            det_conf = 0.90
        else:
            det_conf = 0.75

        # Determine transparent complexity classification
        if is_scanned or visual_density > 8.0:
            complexity_level = "HIGH"
        elif multi_col_detected or total_images_count > 3 or visual_density > 2.0:
            complexity_level = "MEDIUM"
        else:
            complexity_level = "LOW"

        profile = DocumentComplexityProfile(
            scanned_page_ratio=scanned_ratio,
            multi_column_detected=multi_col_detected,
            figure_count=total_images_count,
            table_count=0,
            equation_count=0,
            vector_graphics_count=total_drawings,
            reading_order_conflicts=0,
            extraction_confidence=det_conf,
            visual_density=visual_density,
            complexity_level=complexity_level
        )
        report["complexity_profile"] = profile.model_dump()

    except Exception as e:
        report["valid"] = False
        report["error_message"] = str(e)
    finally:
        if doc:
            doc.close()

    return report

