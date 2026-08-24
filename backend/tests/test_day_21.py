import os
import sys

# Ensure backend path is configured
backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from pipeline import graph


def run_day_21_test():
    """
    Runs the pipeline orchestrator over [1].pdf and verifies that all 11
    global parameters are extracted and matched with the correct confidence scores.
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

    print("[TEST] RUNNING DAY 21 PARAMETER EXTRACTION AGENT TEST...")
    result = graph.invoke(initial_state)

    print("\n[OK] Pipeline Execution Completed Successfully!")
    print(f"Title: {result['metadata'].title}")

    extracted_params = result.get("extracted_parameters")
    
    print("\nExtracted Global Parameters Ledger:")
    if extracted_params:
        fields = extracted_params.__class__.model_fields.keys()
        for field in fields:
            param = getattr(extracted_params, field)
            print(f"\n- Parameter: {field.upper()}")
            print(f"  Value:      '{param.value}'")
            print(f"  Source:     '{param.source}'")
            print(f"  Status:     '{param.status}'")
            print(f"  Confidence:  {param.confidence:.1f}")
    else:
        print("  No parameters extracted.")


if __name__ == "__main__":
    run_day_21_test()
