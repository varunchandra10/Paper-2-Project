import os
import json
import sys

# Add parent directory to path to allow importing from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from schemas import ComponentGraph
from agents.decomposition_agent import graph

def test_decomposition():
    input_json_path = "backend/papers/vlcd_paper_parsed.json"
    
    if not os.path.exists(input_json_path):
        print(f"Error: Parsed paper JSON not found at '{input_json_path}'. Please run parser test first.", file=sys.stderr)
        sys.exit(1)

    print("Loading parsed paper sections...")
    with open(input_json_path, "r", encoding="utf-8") as f:
        parsed_data = json.load(f)

    print("Invoking LangGraph Method Decomposition Agent flow...")
    initial_state = {"parsed_sections": parsed_data}
    
    # Run graph
    result = graph.invoke(initial_state)
    component_graph = result.get("component_graph")

    if component_graph:
        output_path = "backend/papers/vlcd_paper_components.json"
        
        # Save output structured Pydantic model
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(component_graph.model_dump(), f, indent=4, ensure_ascii=False)
            
        print("\n=== DECOMPOSITION SUCCESSFUL ===")
        print(f"Total Components Extracted: {len(component_graph.components)}")
        
        print("\nList of extracted components:")
        for idx, comp in enumerate(component_graph.components, 1):
            print(f"\n[{idx}] Name: {comp.name}")
            print(f"    Type: {comp.type}")
            print(f"    Description: {comp.description}")
            print(f"    Inputs: {comp.inputs}")
            print(f"    Outputs: {comp.outputs}")
            if comp.parameters:
                print("    Parameters:")
                for param_name, details in comp.parameters.items():
                    print(f"        - {param_name}:")
                    print(f"            Value: {details.value}")
                    print(f"            Confidence: {details.confidence}")
                    print(f"            Rationale: {details.rationale}")
                
        print(f"\nSaved structured component graph to: {output_path}")
    else:
        print("Error: Failed to decompose method section.", file=sys.stderr)

if __name__ == "__main__":
    test_decomposition()
