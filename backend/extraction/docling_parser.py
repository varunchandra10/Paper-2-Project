import os
from typing import List, Dict, Any
from core import logger, generate_paper_id


_CONVERTER = None


def extract_docling(pdf_path: str) -> dict:
    """
    Converts a PDF file into a layout-aware Markdown structure and
    extracts structured tables using the Docling DocumentConverter.
    """
    global _CONVERTER
    filename = os.path.basename(pdf_path)
    base_name = os.path.splitext(filename)[0]
    paper_id = generate_paper_id(base_name)
    
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
        logger.info(f"Initializing Docling DocumentConverter for '{filename}'...")
        # Import lazily to prevent CPU/memory overhead if Docling is not invoked
        if _CONVERTER is None:
            from docling.document_converter import DocumentConverter
            _CONVERTER = DocumentConverter()
        
        logger.info(f"Converting PDF '{filename}' via Docling...")
        result = _CONVERTER.convert(pdf_path)
        
        # Export full document as Markdown with element-based fallback
        markdown_text = ""
        try:
            markdown_text = result.document.export_to_markdown()
        except Exception as md_err:
            logger.warning(f"Docling export_to_markdown failed: {md_err}. Reconstructing text from document layout tree.")
            # Fall back to iterating items and reassembling paragraphs/headings
            reconstructed_lines = []
            try:
                for element, _ in result.document.iterate_items():
                    # Check text elements
                    label = getattr(element, "label", "")
                    text_content = getattr(element, "text", "").strip()
                    if text_content:
                        if label == "heading":
                            reconstructed_lines.append(f"\n## {text_content}\n")
                        else:
                            reconstructed_lines.append(text_content)
                markdown_text = "\n\n".join(reconstructed_lines)
            except Exception as item_err:
                logger.error(f"Failed to iterate Docling items: {item_err}")
                
        report["markdown"] = markdown_text
        report["valid"] = True
        
        # Extract structured tables
        tables = []
        try:
            # Docling exports tables cleanly. We scan document elements for table objects.
            table_idx = 1
            for element, _ in result.document.iterate_items():
                if getattr(element, "label", None) == "table":
                    # Convert docling table to pandas dataframe if possible
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
                    except Exception as df_err:
                        # Fallback: get raw table text if dataframe conversion fails
                        table_text = getattr(element, "text", "")
                        if table_text:
                            tables.append({
                                "table_num": table_idx,
                                "caption": f"Table {table_idx}",
                                "content_markdown": f"```\n{table_text}\n```"
                            })
                            table_idx += 1
        except Exception as table_err:
            logger.warning(f"Could not extract individual tables: {table_err}")
            
        report["tables"] = tables
        logger.info(f"Docling conversion completed successfully for '{filename}'.")

    except Exception as e:
        report["valid"] = False
        report["error_message"] = f"Docling conversion failed: {e}"
        logger.error(report["error_message"])
        
    return report
