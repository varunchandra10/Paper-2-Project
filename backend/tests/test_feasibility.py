import os
import json
import sys
import subprocess
import re
import multiprocessing

# Add parent directory to path to allow importing from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from schemas import PipelineOutput
from agents.feasibility_agent import graph

from utils import detect_gpu, detect_system_ram

def test_feasibility():
    input_json_path = "backend/papers/vlcd_full_pipeline_output.json"
    
    if not os.path.exists(input_json_path):
        print(f"Error: Pipeline output JSON not found at '{input_json_path}'. Please run pipeline test first.", file=sys.stderr)
        sys.exit(1)

    print("Loading pipeline output component graph...")
    with open(input_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Parse into PipelineOutput Pydantic model
    pipeline_output = PipelineOutput(**data)
    component_graph = pipeline_output.component_graph

    # Dynamically detect hardware specs
    gpu_name, vram_gb = detect_gpu()
    ram_gb = detect_system_ram()
    cpu_cores = multiprocessing.cpu_count()

    user_constraints = {
        "available_vram_gb": vram_gb,
        "gpu_model": gpu_name,
        "system_ram_gb": ram_gb,
        "cpu_cores": cpu_cores,
        "dataset_size_images": 20000,
        "timeline_weeks": 2
    }

    print(f"\n[Dynamic System Profiler] Detected Hardware Specs:")
    print(f"  - GPU Model: {user_constraints['gpu_model']}")
    print(f"  - Available VRAM: {user_constraints['available_vram_gb']} GB")
    print(f"  - System Memory (RAM): {user_constraints['system_ram_gb']} GB")
    print(f"  - CPU Cores: {user_constraints['cpu_cores']} logical processors")
    print(f"  - Target Dataset Size: {user_constraints['dataset_size_images']} image pairs")
    print(f"  - Target Timeline: {user_constraints['timeline_weeks']} weeks")

    print("\nInvoking LangGraph Feasibility Agent flow...")
    initial_state = {
        "component_graph": component_graph,
        "constraints": user_constraints
    }
    
    # Run graph
    result = graph.invoke(initial_state)
    report = result.get("report")

    if report:
        output_path = "backend/papers/vlcd_feasibility_report.json"
        
        # Save output structured Pydantic model
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(), f, indent=4, ensure_ascii=False)
            
        print("\n=== FEASIBILITY VALIDATION COMPLETE ===")
        print(f"Overall Feasibility Status: {report.overall_status}")
        
        print("\nComponents Analysis:")
        for comp in report.components_analysis:
            print(f"  - {comp.component_name}:")
            print(f"      Status: {comp.status}")
            print(f"      Reason: {comp.reason}")
            print(f"      Suggested Swap: {comp.suggested_substitute}")
            
        print("\nTraining Regime Analysis:")
        print(f"  Status: {report.training_status}")
        print(f"  Reason: {report.training_reason}")
        print(f"  Suggested Swap: {report.training_substitute}")
        
        print("\nRecommendations Summary:")
        for idx, rec in enumerate(report.recommendations, 1):
            print(f"  [{idx}] {rec}")
            
        if report.alternatives:
            print("\n💡 Suggested Cloud Alternatives (To run or scale your project for free):")
            for idx, alt in enumerate(report.alternatives, 1):
                print(f"  [{idx}] Platform: {alt.platform_name}")
                print(f"      Description: {alt.description}")
                print(f"      How to Use: {alt.how_to_use}")
            
        print(f"\nSaved feasibility report JSON to: {output_path}")
    else:
        print("Error: Feasibility validation returned empty report.", file=sys.stderr)

if __name__ == "__main__":
    test_feasibility()
