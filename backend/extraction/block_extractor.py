import os
import fitz  # PyMuPDF
from typing import List, Dict, Any
from core import logger, generate_paper_id
from extraction.pymupdf_parser import (
    detect_pdf_layout,
    extract_blocks_two_column,
    extract_blocks_single_column,
    clean_text
)


def _get_block_font_info(page, bbox) -> tuple:
    """
    Scans the spans inside the page dictionary that overlap with bbox,
    and returns the most common font name and size in that block.
    """
    font_counts = {}
    size_counts = {}
    
    try:
        page_dict = page.get_text("dict")
        x0, y0, x1, y1 = bbox
        
        for b in page_dict.get("blocks", []):
            if b.get("type") != 0:  # text blocks only
                continue
            
            # Check overlap
            bx0, by0, bx1, by1 = b["bbox"]
            # If coordinates match or have significant overlap
            if bx0 >= x0 - 2 and bx1 <= x1 + 2 and by0 >= y0 - 2 and by1 <= y1 + 2:
                for line in b.get("lines", []):
                    for span in line.get("spans", []):
                        f_name = span.get("font", "Unknown")
                        f_size = round(span.get("size", 10.0), 1)
                        span_len = len(span.get("text", ""))
                        
                        font_counts[f_name] = font_counts.get(f_name, 0) + span_len
                        size_counts[f_size] = size_counts.get(f_size, 0) + span_len
                        
    except Exception as e:
        pass

    # Fall back to defaults if no spans matched
    font_name = max(font_counts, key=font_counts.get) if font_counts else "Times-Roman"
    font_size = max(size_counts, key=size_counts.get) if size_counts else 10.0
    
    return font_name, font_size


def extract_document_blocks(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Parses a PDF file and extracts a list of page objects containing structured text blocks,
    preserving layout order and coordinate bounding boxes.
    """
    if not os.path.exists(pdf_path):
        logger.error(f"File not found at: {pdf_path}")
        return []

    doc = fitz.open(pdf_path)
    layout = detect_pdf_layout(pdf_path)
    block_extractor = extract_blocks_two_column if layout == "two_column" else extract_blocks_single_column

    logger.info(f"Extracting blocks from PDF '{os.path.basename(pdf_path)}' using {layout} layout...")
    
    document_pages = []
    
    try:
        for idx in range(len(doc)):
            page = doc.load_page(idx)
            page_num = idx + 1
            page_width = page.rect.width
            page_height = page.rect.height
            
            raw_blocks = block_extractor(page)
            structured_blocks = []
            
            for b_idx, b in enumerate(raw_blocks):
                bbox = [b[0], b[1], b[2], b[3]]
                raw_text = b[4]
                cleaned = clean_text(raw_text)
                if not cleaned:
                    continue
                    
                # Extract primary font details for this block
                font_name, font_size = _get_block_font_info(page, bbox)
                
                block_id = f"p{page_num}_b{b_idx + 1}"
                
                structured_blocks.append({
                    "block_id": block_id,
                    "bbox": [round(c, 2) for c in bbox],
                    "text": cleaned,
                    "font_name": font_name,
                    "font_size": font_size
                })
                
            document_pages.append({
                "page": page_num,
                "width": round(page_width, 1),
                "height": round(page_height, 1),
                "blocks": structured_blocks
            })
            
    except Exception as e:
        logger.error(f"Error extracting blocks: {e}")
    finally:
        doc.close()
        
    return document_pages
