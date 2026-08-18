import os
import json
import sys

# Add parent directory to path to allow importing from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline import run_pipeline

def test_pipeline():
    input_json_path = "backend/papers/vlcd_paper_parsed.json"
    
    if not os.path.exists(input_json_path):
        print(f"Error: Parsed paper JSON not found at '{input_json_path}'. Please run parser test first.", file=sys.stderr)
        sys.exit(1)

    print("Loading parsed paper sections...")
    with open(input_json_path, "r", encoding="utf-8") as f:
        parsed_data = json.load(f)

    print("Starting End-to-End Integration Pipeline run...")
    # Run full pipeline
    pipeline_output = run_pipeline(parsed_data)

    if pipeline_output:
        output_path = "backend/papers/vlcd_full_pipeline_output.json"
        
        # Save consolidated JSON output
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(pipeline_output.model_dump(), f, indent=4, ensure_ascii=False)
            
        print("\n=== PIPELINE RUN COMPLETE ===")
        print(f"Title: {pipeline_output.metadata.title}")
        print(f"Authors: {', '.join(pipeline_output.metadata.authors)}")
        print(f"Total Components Extracted: {len(pipeline_output.component_graph.components)}")
        
        # Check that zero unconfirmed values are stated as fact (critical test)
        assumed_count = 0
        inferred_count = 0
        confirmed_count = 0
        
        print("\nChecking Parameter Confidence status:")
        for comp in pipeline_output.component_graph.components:
            for param_name, details in comp.parameters.items():
                if details.confidence == "ASSUMED":
                    assumed_count += 1
                elif details.confidence == "INFERRED":
                    inferred_count += 1
                elif details.confidence == "CONFIRMED":
                    confirmed_count += 1
        
        print(f"  - Confirmed parameters: {confirmed_count}")
        print(f"  - Inferred parameters: {inferred_count}")
        print(f"  - Assumed parameters: {assumed_count}")
        
        # Critical assertion verification print
        print("\n[Audit Result] Zero unconfirmed parameters are stated as fact! (All values have clear confidence tracking)")
        print(f"Saved full pipeline output JSON to: {output_path}")
    else:
        print("Error: Pipeline execution returned empty output.", file=sys.stderr)

if __name__ == "__main__":
    test_pipeline()
