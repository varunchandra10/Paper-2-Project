import os
import sys

# Configure paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from pipeline import run_refinement
from schemas import ComponentGraph, Component, ParameterDetails, FeasibilityReport

def test_day_26_refinement():
    print("==========================================================")
    print("RUNNING DAY 26 REFINEMENT SYSTEM VERIFICATION TEST")
    print("==========================================================")

    # 1. Setup mock component graph containing paper original parameters
    mock_graph = ComponentGraph(
        components=[
            Component(
                name="Training Hyperparameters",
                type="training",
                description="Hyperparameters for baseline training",
                inputs=[],
                outputs=[],
                parameters={
                    "batch_size": ParameterDetails(value="16", confidence="CONFIRMED", rationale="Extracted from Section IV-A"),
                    "input_size": ParameterDetails(value="256x256", confidence="CONFIRMED", rationale="Extracted from Section IV-A"),
                    "backbone": ParameterDetails(value="Swin-B", confidence="CONFIRMED", rationale="Extracted from Section III-A")
                }
            )
        ]
    )

    # 2. Setup feasibility report signaling warnings
    mock_feasibility = FeasibilityReport(
        overall_status="FEASIBLE_WITH_MODIFICATION",
        components_analysis=[],
        training_status="FEASIBLE_WITH_MODIFICATION",
        training_reason="Training epochs are high for local GPU limitations.",
        training_substitute="Reduce batch size and implement gradient accumulation steps.",
        recommendations=["Freeze backbones to reduce footprint."],
        alternatives=[]
    )

    # 3. Execute refinement adaptation
    print("\nExecuting hyperparameter refinement adaptation...")
    refined_graph = run_refinement(mock_graph, mock_feasibility)
    comp = refined_graph.components[0]

    # 4. Display results
    print("\n--- REFINED PARAMETERS AND RATIONALES ---")
    for key, param in comp.parameters.items():
        print(f"  * {key.upper():<25} : value='{param.value:<10}'")
        print(f"    Rationale                 : {param.rationale}")

    # 5. Assertions
    assert comp.parameters["batch_size"].value == "4"
    assert "PAPER ORIGINAL" in comp.parameters["batch_size"].rationale
    assert "HARDWARE ADAPTATION" in comp.parameters["batch_size"].rationale

    assert comp.parameters["input_size"].value == "128x128"
    assert "PAPER ORIGINAL" in comp.parameters["input_size"].rationale
    assert "HARDWARE ADAPTATION" in comp.parameters["input_size"].rationale

    assert comp.parameters["backbone"].value == "Swin-T"
    assert "PAPER ORIGINAL" in comp.parameters["backbone"].rationale
    assert "HARDWARE ADAPTATION" in comp.parameters["backbone"].rationale

    assert comp.parameters["gradient_accumulation"].value == "4"
    assert comp.parameters["freeze_backbone"].value == "True"
    assert comp.parameters["mixed_precision"].value == "fp16"

    print("\n==========================================================")
    print("[OK] SUCCESS: DAY 26 REFINEMENT SYSTEM VERIFIED AND PASSED!")
    print("==========================================================")

if __name__ == "__main__":
    test_day_26_refinement()
