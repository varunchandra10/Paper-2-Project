import fitz  # PyMuPDF
import re
import json
import os
import sys

def clean_text(text: str) -> str:
    """Cleans up white spaces, duplicate newlines, and ligatures."""
    text = re.sub(r'\n+', '\n', text)
    text = re.sub(r' +', ' ', text)
    # Remove soft hyphens at line wraps (e.g. multi-line words)
    text = re.sub(r'(\w+)-\n(\w+)', r'\1\2', text)
    return text.strip()

def parse_pdf(pdf_path: str):
    """
    Parses a PDF file page-by-page, groups text into sections,
    and prunes out bibliography/references/acknowledgments.
    """
    if not os.path.exists(pdf_path):
        print(f"Error: File not found at {pdf_path}", file=sys.stderr)
        return None

    doc = fitz.open(pdf_path)
    print(f"Parsing PDF: {pdf_path} ({len(doc)} pages)...")

    # Header pattern matches common academic headers:
    # - "1. Introduction", "1.1 Swin Transformer", "I. INTRODUCTION", "Abstract"
    header_regex = re.compile(
        r'^\s*(?:'
        r'(?:[0-9]+(?:\.[0-9]+)*\.?\s+)'  # Numeric hierarchy: 1. or 1.1 or 2.3.1
        r'|(?:[IVXLCDM]+\.\s+)'            # Roman numeral hierarchy: I. or II. or IV.
        r')?('
        r'Abstract|Introduction|Related\s+Work(?:s)?|Method(?:ology)?|System|Proposed\s+Method|'
        r'Architecture|Experiment(?:s)?|Result(?:s)?|Discussion|Conclusion(?:s)?|'
        r'Acknowledgment(?:s)?|Reference(?:s)?|Bibliography'
        r')\b', re.IGNORECASE
    )

    sections = {}
    current_section = "Metadata / Front Matter"
    current_content = []

    prune_keywords = ["references", "bibliography", "acknowledgment", "acknowledgements"]
    pruning_triggered = False

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        
        # Get blocks. fitz returns them in natural reading order (handling double columns).
        # Block tuple structure: (x0, y0, x1, y1, "text", block_no, block_type)
        blocks = page.get_text("blocks")
        
        # Sort blocks by block_no to ensure sequential reading order
        blocks.sort(key=lambda x: x[5])

        for b in blocks:
            # block_type 0 is text. Block_type 1 is image. Ignore images.
            if b[6] != 0:
                continue

            text = b[4].strip()
            if not text:
                continue

            # Split block into lines to inspect the first line
            lines = text.split('\n')
            first_line = lines[0].strip()

            # We identify a header if the block's first line matches the regex,
            # and the block is relatively short (headers don't contain long body text in one block).
            match = header_regex.match(first_line)
            is_heading = False
            if match and len(lines) <= 2 and len(text) < 100:
                is_heading = True
                header_title = text.replace('\n', ' ').strip()
                
                # Check if this heading signals that we should prune the rest of the document
                header_lower = header_title.lower()
                if any(kw in header_lower for kw in prune_keywords):
                    # Save the accumulated content of the previous section before breaking
                    if current_content:
                        sections[current_section] = clean_text("\n".join(current_content))
                    pruning_triggered = True
                    print(f"Detected pruning section: '{header_title}'. Pruning subsequent text.")
                    break

                # Save the accumulated content of the previous section
                if current_content:
                    sections[current_section] = clean_text("\n".join(current_content))
                
                current_section = header_title
                current_content = lines[1:] if len(lines) > 1 else []
            
            if pruning_triggered:
                break

            if not is_heading:
                current_content.append(text)

        if pruning_triggered:
            break

    # Save the final section
    if current_content and not pruning_triggered:
        sections[current_section] = clean_text("\n".join(current_content))

    return sections

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Parse PDF into sections and prune citations.")
    parser.add_argument("pdf_path", type=str, nargs="?", default="backend/papers/vlcd_paper.pdf",
                        help="Path to the PDF file to parse.")
    args = parser.parse_args()

    parsed_sections = parse_pdf(args.pdf_path)
    if parsed_sections:
        output_path = args.pdf_path.replace(".pdf", "_parsed.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(parsed_sections, f, indent=4, ensure_ascii=False)
        print(f"\nSuccessfully parsed {len(parsed_sections)} sections.")
        print(f"Saved parsed JSON to: {output_path}")
        print("\nExtracted Sections & Character Counts:")
        for sec, content in parsed_sections.items():
            print(f" - {sec}: {len(content)} characters")
