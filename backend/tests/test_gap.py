import os
import json
import sys

# Add parent directory to path to allow importing from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from schemas import ComponentGraph
from agents.gap_agent import graph

def test_gap_agent():
    input_json_path = "backend/papers/vlcd_paper_components.json"
    
    if not os.path.exists(input_json_path):
        print(f"Error: Component graph JSON not found at '{input_json_path}'. Please run decomposition test first.", file=sys.stderr)
        sys.exit(1)

    print("Loading component graph...")
    with open(input_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Parse into Pydantic model
    component_graph = ComponentGraph(**data)

    print("Invoking LangGraph Gap-Finding Agent flow...")
    initial_state = {"component_graph": component_graph}
    
    # Run graph
    result = graph.invoke(initial_state)
    updated_graph = result.get("component_graph")

    if updated_graph:
        output_path = "backend/papers/vlcd_paper_gap_filled.json"
        
        # Save output structured Pydantic model
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(updated_graph.model_dump(), f, indent=4, ensure_ascii=False)
            
        print("\n=== GAP FILLING SUCCESSFUL ===")
        print(f"Total Components Scanned: {len(updated_graph.components)}")
        
        print("\nParameter Confidence Status:")
        for idx, comp in enumerate(updated_graph.components, 1):
            print(f"\n[{idx}] Component: {comp.name}")
            for param_name, details in comp.parameters.items():
                print(f"    - {param_name}:")
                print(f"        Value: {details.value}")
                print(f"        Confidence: {details.confidence}")
                print(f"        Rationale: {details.rationale}")
                
        print(f"\nSaved gap-filled component graph to: {output_path}")
    else:
        print("Error: Failed to fill gaps in component graph.", file=sys.stderr)

if __name__ == "__main__":
    test_gap_agent()
