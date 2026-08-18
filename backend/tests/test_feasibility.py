import os
import json
import sys
import subprocess
import re
import multiprocessing

# Add parent directory to path to allow importing from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from schemas import PipelineOutput
from feasibility_agent import graph

def detect_gpu_nvismi():
    """Detects NVIDIA GPU details using nvidia-smi utility directly."""
    # Attempt 1: Run directly from PATH
    try:
        cmd = ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"]
        output = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
        line = output.strip().split('\n')[0]
        if ',' in line:
            name, mem_str = line.split(',', 1)
            vram_gb = float(mem_str.strip()) / 1024.0
            return name.strip(), round(vram_gb, 1)
    except:
        pass
    
    # Attempt 2: Check standard installation path if not in PATH
    try:
        abs_path = r"C:\Program Files\NVIDIA Corporation\NVSMI\nvidia-smi.exe"
        if os.path.exists(abs_path):
            cmd = [abs_path, "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"]
            output = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
            line = output.strip().split('\n')[0]
            if ',' in line:
                name, mem_str = line.split(',', 1)
                vram_gb = float(mem_str.strip()) / 1024.0
                return name.strip(), round(vram_gb, 1)
    except:
        pass
    return None, None

def detect_gpu():
    """Tries to query PyTorch for GPU details, falls back to nvidia-smi."""
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            return gpu_name, round(vram_gb, 1)
    except:
        pass
    
    # Fallback to nvidia-smi
    name, vram = detect_gpu_nvismi()
    if name:
        return name, round(vram, 1)
    return "CPU Only / Integrated Graphics", 0.0

def detect_system_ram():
    """Detects physical system RAM in GB using PowerShell CIM query (Windows 11 compliant)."""
    try:
        cmd = ["powershell", "-Command", "(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory"]
        output = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
        ram_bytes = float(output.strip())
        return round(ram_bytes / (1024**3), 1)
    except:
        pass
    return 16.0 # safe default fallback

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
            
        print(f"\nSaved feasibility report JSON to: {output_path}")
    else:
        print("Error: Feasibility validation returned empty report.", file=sys.stderr)

if __name__ == "__main__":
    test_feasibility()
