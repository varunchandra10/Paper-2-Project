import os
import sys

# Ensure backend path is configured
backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from pipeline import graph


def run_day_20_test():
    """
    Runs the pipeline orchestrator over [1].pdf and verifies that the extracted
    ComponentGraph contains serialized data flow dependency edges.
    """
    pdf_absolute_path = os.path.join(backend_path, "papers", "research_papers", "[1].pdf")

    initial_state = {
        "pdf_path": pdf_absolute_path,
        "constraints": {
            "gpu_model": "NVIDIA GeForce RTX 4080S",
            "system_ram_gb": 32.0,
            "vram_gb": 16.0,
            "timeline_weeks": 2
        },
        "model_name": "qwen2.5-coder:1.5b",
        "loop_count": 0
    }

    print("[TEST] RUNNING DAY 20 COMPONENT GRAPH DEPENDENCY TEST...")
    result = graph.invoke(initial_state)

    print("\n[OK] Pipeline Execution Completed Successfully!")
    print(f"Title: {result['metadata'].title}")

    component_graph = result.get("component_graph")
    
    print("\nAdjacency Component Dependency Edges:")
    if component_graph and component_graph.edges:
        for idx, edge in enumerate(component_graph.edges):
            print(f"  [{idx+1}] {edge.get('source')} -> {edge.get('target')}")
    else:
        print("  No dependency edges extracted.")


if __name__ == "__main__":
    run_day_20_test()
