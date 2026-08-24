import os
import sys

# Ensure backend path is configured
backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from pipeline import graph


def run_day_22_test():
    """
    Runs the pipeline orchestrator over [1].pdf and verifies:
    1. Day 20 dependency edges.
    2. Day 21 global parameters.
    3. Day 22 parameter gap classifications.
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

    print("[TEST] RUNNING COMPLETE INGESTION, DECOMPOSITION & GAP FINDING AUDIT...")
    result = graph.invoke(initial_state)

    print("\n[OK] Pipeline Execution Completed Successfully!")
    print(f"Title: {result['metadata'].title}")

    # 1. Day 20 Component Graph edges
    component_graph = result.get("component_graph")
    print("\n==================================================")
    print("DAY 20: Serialized Component Dependency Edges:")
    print("==================================================")
    if component_graph and component_graph.edges:
        for idx, edge in enumerate(component_graph.edges):
            print(f"  [{idx+1}] {edge.get('source')} -> {edge.get('target')}")
    else:
        print("  No dependency edges found.")

    # 2. Day 21 Extracted Parameters
    extracted_params = result.get("extracted_parameters")
    print("\n==================================================")
    print("DAY 21: Extracted Global Parameters Ledger:")
    print("==================================================")
    if extracted_params:
        fields = extracted_params.__class__.model_fields.keys()
        for field in fields:
            param = getattr(extracted_params, field)
            print(f"  - {field.upper():<15} : value='{param.value:<10}' | status='{param.status:<8}' | conf={param.confidence:.1f}")
    else:
        print("  No parameters extracted.")

    # 3. Day 22 Parameter Gap Classification Report
    gap_report = result.get("gap_report")
    print("\n==================================================")
    print("DAY 22: Parameter Gap Classification Report:")
    print("==================================================")
    if gap_report:
        print(f"Summary: {gap_report.summary}")
        print(f"Has Critical Missing Gaps: {gap_report.has_critical_missing_parameters}")
        print("\nGaps Ledger:")
        for idx, gap in enumerate(gap_report.parameter_gaps, 1):
            print(f"  [{idx}] Parameter: {gap.parameter_name.upper()}")
            print(f"      Classification: {gap.classification}")
            print(f"      Value:          '{gap.value}'")
            print(f"      Details:        {gap.details}\n")
    else:
        print("  No gap report generated.")


if __name__ == "__main__":
    run_day_22_test()
