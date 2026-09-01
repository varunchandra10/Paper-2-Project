import os
import re
from typing import List, Dict, Any

_CONVERTER = None


def get_paper_slug_id(filename: str) -> str:
    base_name = os.path.splitext(filename)[0]
    clean_title = re.sub(r'[^a-z0-9\s]', '', base_name.lower()).strip()
    slug = re.sub(r'\s+', '_', clean_title)[:30].strip('_')
    return f"paper_{slug}" if slug else "paper_document"


def extract_docling(pdf_path: str) -> dict:
    """
    Converts a PDF file into a layout-aware Markdown structure and
    extracts structured tables using Docling if available.
    """
    global _CONVERTER
    filename = os.path.basename(pdf_path)
    paper_id = get_paper_slug_id(filename)
    
    report = {
        "paper_id": paper_id,
        "filename": filename,
        "valid": False,
        "markdown": "",
        "tables": [],
        "error_message": None
    }
    
    if not os.path.exists(pdf_path):
        report["error_message"] = f"File not found at path: {pdf_path}"
        return report

    try:
        if _CONVERTER is None:
            from docling.document_converter import DocumentConverter
            _CONVERTER = DocumentConverter()
        
        result = _CONVERTER.convert(pdf_path)
        markdown_text = ""
        try:
            markdown_text = result.document.export_to_markdown()
        except Exception:
            reconstructed_lines = []
            try:
                for element, _ in result.document.iterate_items():
                    label = getattr(element, "label", "")
                    text_content = getattr(element, "text", "").strip()
                    if text_content:
                        if label == "heading":
                            reconstructed_lines.append(f"\n## {text_content}\n")
                        else:
                            reconstructed_lines.append(text_content)
                markdown_text = "\n\n".join(reconstructed_lines)
            except Exception:
                pass
                
        report["markdown"] = markdown_text
        report["valid"] = True
        
        tables = []
        try:
            table_idx = 1
            for element, _ in result.document.iterate_items():
                if getattr(element, "label", None) == "table":
                    try:
                        df = element.export_to_dataframe()
                        if df is not None and not df.empty:
                            table_md = df.to_markdown(index=False)
                            caption = getattr(element, "caption", f"Table {table_idx}")
                            tables.append({
                                "table_num": table_idx,
                                "caption": caption,
                                "content_markdown": table_md
                            })
                            table_idx += 1
                    except Exception:
                        table_text = getattr(element, "text", "")
                        if table_text:
                            tables.append({
                                "table_num": table_idx,
                                "caption": f"Table {table_idx}",
                                "content_markdown": f"```\n{table_text}\n```"
                            })
                            table_idx += 1
        except Exception:
            pass
            
        report["tables"] = tables

    except Exception as e:
        report["valid"] = False
        report["error_message"] = f"Docling conversion skipped/unavailable: {e}"
        
    return report
