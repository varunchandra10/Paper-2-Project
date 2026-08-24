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
from schemas import ExtractedParameters, ProjectParameter

def test_day_24_estimator():
    print("==========================================================")
    print("RUNNING DAY 24 RESOURCE ESTIMATOR VERIFICATION TEST")
    print("==========================================================")

    # 1. Gather hardware specs profile
    profile = profile_hardware()

    # 2. Mock extracted parameters ledger
    mock_params = ExtractedParameters(
        model=ProjectParameter(value="Swin-T backbone", source="Section III-A, Page 4", status="EXPLICIT", confidence=1.0),
        dataset=ProjectParameter(value="LEVIR-CD", source="Section IV-A, Page 8", status="EXPLICIT", confidence=1.0),
        optimizer=ProjectParameter(value="AdamW", source="Section IV-A, Page 8", status="EXPLICIT", confidence=1.0),
        learning_rate=ProjectParameter(value="2e-4", source="Section IV-A, Page 8", status="EXPLICIT", confidence=1.0),
        batch_size=ProjectParameter(value="16", source="Section IV-A, Page 8", status="EXPLICIT", confidence=1.0),
        epochs=ProjectParameter(value="50", source="Section IV-A, Page 8", status="EXPLICIT", confidence=1.0),
        loss=ProjectParameter(value="Binary Cross Entropy", source="Section IV-A, Page 8", status="EXPLICIT", confidence=1.0),
        scheduler=ProjectParameter(value="Cosine Annealing", source="Section IV-A, Page 8", status="EXPLICIT", confidence=1.0),
        input_size=ProjectParameter(value="256x256", source="Section IV-A, Page 8", status="EXPLICIT", confidence=1.0),
        augmentation=ProjectParameter(value="random flip, rotate", source="Section IV-A, Page 8", status="EXPLICIT", confidence=1.0),
        hardware=ProjectParameter(value="NVIDIA RTX 4090", source="Section IV-A, Page 8", status="EXPLICIT", confidence=1.0)
    )

    # 3. Compute resources requirements
    print("\nEstimating requirements for model, dataset, training, inference, and storage...")
    report = estimate_resources(mock_params, profile)
    report_dict = report.model_dump()

    # 4. Display results
    print("\n--- MODEL RESOURCE SPECIFICATIONS ---")
    print(json.dumps(report_dict["model"], indent=2))

    print("\n--- DATASET RESOURCE SPECIFICATIONS ---")
    print(json.dumps(report_dict["dataset"], indent=2))

    print("\n--- TRAINING RESOURCE SPECIFICATIONS ---")
    print(json.dumps(report_dict["training"], indent=2))

    print("\n--- INFERENCE RESOURCE SPECIFICATIONS ---")
    print(json.dumps(report_dict["inference"], indent=2))

    print("\n--- STORAGE RESOURCE SPECIFICATIONS ---")
    print(json.dumps(report_dict["storage"], indent=2))

    print(f"\nOverall Complexity/Resource Tier: {report.overall_resource_tier}")

    # 5. Validation Assertions
    assert report.model.param_count_millions > 0.0
    assert report.model.vram_minimum_gb > 0.0
    assert report.dataset.raw_size_gb > 0.0
    assert report.training.vram_recommended_gb > 0.0
    assert report.training.estimated_time_hours > 0.0
    assert report.inference.vram_gb > 0.0
    assert report.storage.required_disk_gb > 0.0
    assert report.overall_resource_tier in ["LOW", "MEDIUM", "HIGH", "EXTREME"]

    print("\n==========================================================")
    print("[OK] SUCCESS: DAY 24 RESOURCE ESTIMATOR VERIFIED AND PASSED!")
    print("==========================================================")

if __name__ == "__main__":
    test_day_24_estimator()
