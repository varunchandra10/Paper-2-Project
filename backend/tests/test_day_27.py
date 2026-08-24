import os
import sys
import json

# Configure paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from agents.sequencing_agent import run_sequencing_agent
from schemas import ComponentGraph, Component, FeasibilityReport

def test_day_27_sequencing():
    print("==========================================================")
    print("RUNNING DAY 27 BUILD SEQUENCING VERIFICATION TEST")
    print("==========================================================")

    # 1. Setup mock component graph
    mock_graph = ComponentGraph(
        components=[
            Component(name="Swin-T backbone encoder", type="encoder", inputs=["input_image"], outputs=["feature_map"], description="Feature extraction network.", parameters={}),
            Component(name="Bilinear Interpolation Fusion", type="fusion", inputs=["feature_map"], outputs=["fused_map"], description="Fuses multi-scale maps.", parameters={}),
            Component(name="Change Decoder", type="decoder", inputs=["fused_map"], outputs=["change_mask"], description="Predicts change mask.", parameters={})
        ]
    )

    # 2. Setup mock feasibility report
    mock_feasibility = FeasibilityReport(
        overall_status="FEASIBLE_WITH_MODIFICATION",
        components_analysis=[],
        training_status="FEASIBLE_WITH_MODIFICATION",
        training_reason="Training epochs are high for local GPU limitations.",
        training_substitute="Reduce batch size and implement gradient accumulation steps.",
        recommendations=["Freeze backbones to reduce footprint."],
        alternatives=[]
    )

    # 3. Generate Build Sequence milestones
    print("\nGenerating build milestones sequence from graph and feasibility parameters...")
    build_sequence = run_sequencing_agent(mock_graph, mock_feasibility)

    # 4. Display sequencing plan
    print(f"\nTotal Implementation Duration: {build_sequence.total_duration_weeks} Weeks")
    print("\nMilestones List:")
    for ms in build_sequence.milestones:
        print(f"  [Milestone {ms.id}] {ms.name} ({ms.estimated_complexity} Complexity)")
        print(f"    Core Objectives : {ms.objectives}")
        print(f"    Involved Modules: {ms.components_involved}")
        print(f"    Rationals       : {ms.dependency_rationale}\n")

    # 5. Assertions
    assert len(build_sequence.milestones) > 0
    assert build_sequence.total_duration_weeks > 0.0
    
    # Verify that first milestone is data/pipeline setup, and last is model training/scaling
    first_ms = build_sequence.milestones[0]
    last_ms = build_sequence.milestones[-1]
    assert "data" in first_ms.name.lower() or "pipeline" in first_ms.name.lower() or "environment" in first_ms.name.lower()
    assert "training" in last_ms.name.lower() or "scale" in last_ms.name.lower() or "synthesis" in last_ms.name.lower() or "decoder" in last_ms.name.lower()

    print("\n==========================================================")
    print("[OK] SUCCESS: DAY 27 BUILD SEQUENCING VERIFIED AND PASSED!")
    print("==========================================================")

if __name__ == "__main__":
    test_day_27_sequencing()
