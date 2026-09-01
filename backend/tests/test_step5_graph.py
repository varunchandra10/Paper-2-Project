import sys
import os
import pytest

# Add new_backend to python search path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from app.graph.workflow import app_workflow

workspace_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sample_pdf_path = os.path.join(workspace_dir, "[2].pdf")
if not os.path.exists(sample_pdf_path):
    sample_pdf_path = os.path.join(workspace_dir, "backend", "storage", "papers", "2.pdf")
if not os.path.exists(sample_pdf_path):
    sample_pdf_path = os.path.join(workspace_dir, "backend", "storage", "papers", "[2].pdf")


def test_full_langgraph_execution():
    print(f"\n--- Running Full LangGraph Workflow Test on '[2].pdf' ---")
    if not os.path.exists(sample_pdf_path):
        pytest.skip(f"Sample PDF '[2].pdf' not present for test at {sample_pdf_path}")

    initial_state = {
        "pdf_path": sample_pdf_path,
        "constraints": {"max_vram_gb": 6.0},
        "model_name": "qwen2.5-coder:1.5b",
        "loop_count": 0
    }

    print("Invoking compiled StateGraph workflow...")
    final_state = app_workflow.invoke(initial_state)

    print(f"Workflow execution completed!")
    print(f"Paper Title: '{final_state['paper_doc'].metadata.title}'")
    print(f"Feasibility Status: {final_state['feasibility_report'].overall_status}")
    print(f"Build Sequence Steps: {final_state['build_sequence'].total_steps}")
    print(f"Parameters Approved: {final_state.get('parameters_approved')}")

    assert final_state["paper_doc"] is not None
    assert final_state["extracted_parameters"] is not None
    assert final_state["feasibility_report"] is not None
    assert final_state["build_sequence"].total_steps > 0
    assert final_state["parameters_approved"] is True

    print("\nAll Step 5 LangGraph Workflow tests passed successfully!")


if __name__ == "__main__":
    test_full_langgraph_execution()
