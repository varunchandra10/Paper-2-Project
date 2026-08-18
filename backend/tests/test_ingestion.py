import os
import json
import sys

# Add parent directory to path to allow importing from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.ingestion_agent import graph

def test_ingestion():
    input_json_path = "backend/papers/vlcd_paper_parsed.json"
    
    if not os.path.exists(input_json_path):
        print(f"Error: Parsed paper JSON not found at '{input_json_path}'. Please run parser test first.", file=sys.stderr)
        sys.exit(1)

    print("Loading parsed paper sections...")
    with open(input_json_path, "r", encoding="utf-8") as f:
        parsed_data = json.load(f)

    print("Starting Ingestion Agent Flow test...")
    initial_state = {"parsed_sections": parsed_data}
    
    # Run graph
    result = graph.invoke(initial_state)
    metadata = result.get("metadata")

    if metadata:
        output_path = "backend/papers/vlcd_paper_metadata.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(metadata.model_dump(), f, indent=4, ensure_ascii=False)
        print("\n=== EXTRACTION SUCCESSFUL ===")
        print(f"Title: {metadata.title}")
        print(f"Authors: {', '.join(metadata.authors)}")
        print(f"Primary Contribution: {metadata.primary_contribution}")
        print(f"Saved metadata JSON to: {output_path}")
    else:
        print("Error: Failed to extract metadata.", file=sys.stderr)

if __name__ == "__main__":
    test_ingestion()
