import os
import sys
import json

# Configure paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from core.hardware_profiler import profile_hardware
from core.resource_estimator import estimate_resources
from agents.feasibility_agent import run_feasibility_agent
from schemas import ExtractedParameters, ProjectParameter, ComponentGraph, Component

def test_day_25_feasibility():
    print("==========================================================")
    print("RUNNING DAY 25 FEASIBILITY ENGINE VERIFICATION TEST")
    print("==========================================================")

    # 1. Profile system specs
    profile = profile_hardware()

    # 2. Mock component graph
    mock_graph = ComponentGraph(
        components=[
            Component(name="Swin-T backbone encoder", type="encoder", inputs=["input_image"], outputs=["feature_map"], description="Feature extraction network.", parameters={}),
            Component(name="Bilinear Interpolation Fusion", type="fusion", inputs=["feature_map"], outputs=["fused_map"], description="Fuses multi-scale maps.", parameters={}),
            Component(name="Change Decoder", type="decoder", inputs=["fused_map"], outputs=["change_mask"], description="Predicts change mask.", parameters={})
        ]
    )

    # 3. Mock extracted parameters
    mock_params = ExtractedParameters(
        model=ProjectParameter(value="Swin-T backbone", source="Page 4", status="EXPLICIT", confidence=1.0),
        dataset=ProjectParameter(value="LEVIR-CD", source="Page 8", status="EXPLICIT", confidence=1.0),
        optimizer=ProjectParameter(value="AdamW", source="Page 8", status="EXPLICIT", confidence=1.0),
        learning_rate=ProjectParameter(value="2e-4", source="Page 8", status="EXPLICIT", confidence=1.0),
        batch_size=ProjectParameter(value="16", source="Page 8", status="EXPLICIT", confidence=1.0),
        epochs=ProjectParameter(value="50", source="Page 8", status="EXPLICIT", confidence=1.0),
        loss=ProjectParameter(value="Binary Cross Entropy", source="Page 8", status="EXPLICIT", confidence=1.0),
        scheduler=ProjectParameter(value="Cosine Annealing", source="Page 8", status="EXPLICIT", confidence=1.0),
        input_size=ProjectParameter(value="256x256", source="Page 8", status="EXPLICIT", confidence=1.0),
        augmentation=ProjectParameter(value="random flip", source="Page 8", status="EXPLICIT", confidence=1.0),
        hardware=ProjectParameter(value="NVIDIA RTX 4090", source="Page 8", status="EXPLICIT", confidence=1.0)
    )

    # 4. Generate resource estimation
    print("\n[Step 1] Estimating resource footprint...")
    res_report = estimate_resources(mock_params, profile)

    # 5. Evaluate feasibility using resource requirements
    print("[Step 2] Executing Feasibility Engine...")
    feasibility_report = run_feasibility_agent(
        component_graph=mock_graph,
        constraints={
            "gpu_model": profile.gpus[0].name if profile.gpus else "CPU Only",
            "system_ram_gb": profile.ram.total_gb,
            "vram_gb": profile.gpus[0].vram_total_gb if profile.gpus else 0.0,
            "timeline_weeks": 2
        },
        resource_estimation=res_report
    )

    report_dict = feasibility_report.model_dump()

    # 6. Display results
    print("\n--- FEASIBILITY ENGINE RESULTS ---")
    print(f"Overall Status:       {feasibility_report.overall_status}")
    print(f"Training Status:      {feasibility_report.training_status}")
    print(f"Training Reason:      {feasibility_report.training_reason}")
    print(f"Training Substitute:  {feasibility_report.training_substitute}")
    
    print("\nComponents Analysis:")
    for comp in feasibility_report.components_analysis:
        print(f"  - Module: {comp.component_name:<30} | Status: {comp.status:<25}")
        print(f"    Reason: {comp.reason}")
        print(f"    Swap:   {comp.suggested_substitute}\n")

    print("Recommendations:")
    for rec in feasibility_report.recommendations:
        print(f"  * {rec}")

    print("\nAlternative Platforms:")
    for alt in feasibility_report.alternatives:
        print(f"  - Platform: {alt.platform_name}")
        print(f"    Offerings: {alt.description}")
        print(f"    Usage:     {alt.how_to_use}")

    # 7. Assertions
    valid_statuses = ["FEASIBLE", "FEASIBLE_WITH_MODIFICATION", "NOT_FEASIBLE", "UNKNOWN"]
    assert feasibility_report.overall_status in valid_statuses
    assert feasibility_report.training_status in valid_statuses
    assert len(feasibility_report.components_analysis) > 0
    assert len(feasibility_report.recommendations) > 0
    assert len(feasibility_report.alternatives) > 0

    print("\n==========================================================")
    print("[OK] SUCCESS: DAY 25 FEASIBILITY ENGINE VERIFIED AND PASSED!")
    print("==========================================================")

if __name__ == "__main__":
    test_day_25_feasibility()
