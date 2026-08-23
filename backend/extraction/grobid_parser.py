import os
import re
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict, Any
from core import logger, generate_paper_id

NS = {'tei': 'http://www.tei-c.org/ns/1.0'}


def _xml_get_text(element) -> str:
    """Helper to extract all nested text from an XML element, ignoring TEI tags."""
    if element is None:
        return ""
    # Join text and tail recursively
    parts = [element.text or ""]
    for child in element:
        parts.append(_xml_get_text(child))
        parts.append(child.tail or "")
    return "".join(parts).strip()


def extract_grobid(pdf_path: str, grobid_url: str = "http://localhost:8070") -> dict:
    """
    Sends the PDF file to a locally running GROBID instance on port 8070,
    parses the returned TEI/XML string, and structures it into a canonical layout.
    """
    filename = os.path.basename(pdf_path)
    base_name = os.path.splitext(filename)[0]
    paper_id = generate_paper_id(base_name)
    
    report = {
        "paper_id": paper_id,
        "filename": filename,
        "title": "Unknown Title",
        "authors": [],
        "abstract": "",
        "sections": {},
        "tables": [],
        "figures": [],
        "references": [],
        "valid": False,
        "error_message": None
    }
    
    if not os.path.exists(pdf_path):
        report["error_message"] = f"File not found at path: {pdf_path}"
        return report

    # 1. Send the PDF document to the GROBID server
    api_endpoint = f"{grobid_url.rstrip('/')}/api/processFulltextDocument"
    logger.info(f"Sending document '{filename}' to GROBID API: {api_endpoint}...")
    
    try:
        with open(pdf_path, 'rb') as f:
            files = {'input': f}
            # processFulltextDocument parses headers, abstract, sections, references, figures, tables
            response = requests.post(api_endpoint, files=files, timeout=60)
            
        if response.status_code != 200:
            report["error_message"] = f"GROBID server returned status code {response.status_code}: {response.text[:200]}"
            logger.error(report["error_message"])
            return report
            
        # 2. Parse the TEI XML response
        root = ET.fromstring(response.text)
        report["valid"] = True
        
        # --- Metadata: Title ---
        title_elem = root.find(".//tei:titleStmt/tei:title[@type='main']", NS)
        if title_elem is None:
            title_elem = root.find(".//tei:titleStmt/tei:title", NS)
        if title_elem is not None:
            report["title"] = _xml_get_text(title_elem)
            
        # --- Metadata: Authors ---
        author_elems = root.findall(".//tei:sourceDesc/tei:biblStruct/tei:analytic/tei:author", NS)
        authors = []
        for author in author_elems:
            pers_name = author.find("tei:persName", NS)
            if pers_name is not None:
                forenames = [f.text for f in pers_name.findall("tei:forename", NS) if f.text]
                surname_elem = pers_name.find("tei:surname", NS)
                surname = surname_elem.text if surname_elem is not None else ""
                
                full_name = " ".join(forenames + [surname]).strip()
                if full_name:
                    authors.append(full_name)
        report["authors"] = authors
        
        # --- Metadata: Abstract ---
        abstract_p_elems = root.findall(".//tei:profileDesc/tei:abstract//tei:p", NS)
        abstract_paragraphs = [_xml_get_text(p) for p in abstract_p_elems if _xml_get_text(p)]
        report["abstract"] = "\n\n".join(abstract_paragraphs)
        
        # --- Body: Sections & Paragraphs ---
        body_divs = root.findall(".//tei:text/tei:body/tei:div", NS)
        sections = {}
        
        for div in body_divs:
            head_elem = div.find("tei:head", NS)
            head_text = _xml_get_text(head_elem) if head_elem is not None else "Heading"
            
            p_elems = div.findall("tei:p", NS)
            paragraphs = [_xml_get_text(p) for p in p_elems if _xml_get_text(p)]
            
            if paragraphs:
                sections[head_text] = {
                    "content": "\n\n".join(paragraphs),
                    "subsections": {}
                }
        report["sections"] = sections
        
        # --- Body: Tables & Figures ---
        figure_elems = root.findall(".//tei:figure", NS)
        tables = []
        figures = []
        
        for fig in figure_elems:
            fig_id = fig.get("{http://www.w3.org/XML/1998/namespace}id", "fig_unknown")
            fig_desc_elem = fig.find("tei:figDesc", NS)
            fig_desc = _xml_get_text(fig_desc_elem) if fig_desc_elem is not None else ""
            
            # Check if this figure element holds a table
            table_elem = fig.find("tei:table", NS)
            if table_elem is not None:
                tables.append({
                    "id": fig_id,
                    "caption": fig_desc,
                    "content": _xml_get_text(table_elem)
                })
            else:
                figures.append({
                    "id": fig_id,
                    "caption": fig_desc
                })
                
        report["tables"] = tables
        report["figures"] = figures
        
        # --- Formulas / Equations ---
        formula_elems = root.findall(".//tei:formula", NS)
        equations = []
        for formula in formula_elems:
            f_id = formula.get("{http://www.w3.org/XML/1998/namespace}id", "eq_unknown")
            label_elem = formula.find("tei:label", NS)
            label = _xml_get_text(label_elem) if label_elem is not None else ""
            
            # Content is the text directly inside formula (or its math tags if any)
            formula_text = _xml_get_text(formula).strip()
            # If the label is in the text, clean it (e.g. "(1)")
            if label and formula_text.endswith(label):
                formula_text = formula_text[:-len(label)].strip()
                
            if formula_text:
                equations.append({
                    "id": f_id,
                    "latex": formula_text,
                    "caption": f"Equation {label}" if label else "Equation"
                })
        report["equations"] = equations

        # --- References ---
        bib_structs = root.findall(".//tei:back/tei:div[@type='references']//tei:biblStruct", NS)
        references = []
        for bib in bib_structs:
            title_elem = bib.find(".//tei:title[@type='main']", NS)
            if title_elem is not None:
                ref_title = _xml_get_text(title_elem)
                references.append(ref_title)
        report["references"] = references

        # --- Fallback Heuristics for IEEE / Complex Layouts ---
        # Sometimes GROBID parses the paper title/abstract/authors as the first body section
        if (not report["title"] or report["title"].strip() == "Unknown Title") and report["sections"]:
            first_sec_title = list(report["sections"].keys())[0]
            if len(first_sec_title) > 30 and not any(first_sec_title.lower().startswith(p) for p in ["1", "i", "section"]):
                logger.info(f"Applying GROBID misclassification fallback. Title detected: '{first_sec_title}'")
                report["title"] = first_sec_title
                first_sec_data = report["sections"].pop(first_sec_title)
                
                content = first_sec_data["content"]
                
                # Regex match Abstract block
                abstract_match = re.search(r'(?:Abstract|ABSTRACT)\s*[-—:]?\s*(.*)', content, re.DOTALL)
                if abstract_match:
                    report["abstract"] = abstract_match.group(1).strip()
                    
                    # Extract authors (text preceding Abstract)
                    authors_text = content[:abstract_match.start()].strip()
                    if authors_text:
                        # Clean up formatting: e.g. "Author A , Author B , and Author C" -> split into list
                        authors_text = re.sub(r'\s+and\s+', ' , ', authors_text, flags=re.IGNORECASE)
                        parsed_authors = [a.strip() for a in authors_text.split(',') if a.strip()]
                        # Filter out common footnote junk if present
                        report["authors"] = [a for a in parsed_authors if len(a) > 2 and "abstract" not in a.lower()]

    except Exception as e:
        report["valid"] = False
        report["error_message"] = f"Failed to send request or parse GROBID XML: {e}"
        logger.error(report["error_message"])
        
    return report
