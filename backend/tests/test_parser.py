import os
import json
import sys

# Add parent directory to path to allow importing from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from parser import parse_pdf

def test_parser():
    pdf_path = "backend/papers/vlcd_paper.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"Error: Research paper PDF not found at '{pdf_path}'. Please upload it first.", file=sys.stderr)
        sys.exit(1)

    print("Running PDF Parser test...")
    parsed_sections = parse_pdf(pdf_path)
    
    if parsed_sections:
        output_path = "backend/papers/vlcd_paper_parsed.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(parsed_sections, f, indent=4, ensure_ascii=False)
        print(f"\nSuccessfully parsed {len(parsed_sections)} sections.")
        print(f"Saved parsed JSON to: {output_path}")
        print("\nExtracted Sections & Character Counts:")
        for sec, content in parsed_sections.items():
            print(f" - {sec}: {len(content)} characters")
    else:
        print("Error: Failed to parse PDF.", file=sys.stderr)

if __name__ == "__main__":
    test_parser()
