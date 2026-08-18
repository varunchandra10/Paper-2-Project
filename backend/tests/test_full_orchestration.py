import os
import sys
import multiprocessing

# Add parent directory to path to allow importing from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pipeline import graph
from utils import detect_gpu, detect_system_ram

def test_full_orchestration():
    print("==================================================")
    print("         LANGGRAPH ORCHESTRATION PIPELINE         ")
    print("==================================================")
    
    # 1. Dynamically profile system specs
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
    
    print("\n[Orchestrator Test] Detected Hardware Constraints:")
    print(f"  - GPU Model: {user_constraints['gpu_model']}")
    print(f"  - Available VRAM: {user_constraints['available_vram_gb']} GB")
    print(f"  - System Memory: {user_constraints['system_ram_gb']} GB")
    print(f"  - CPU Cores: {user_constraints['cpu_cores']} logical processors")
    print(f"  - Dataset size limit: {user_constraints['dataset_size_images']}")
    print(f"  - Timeline budget: {user_constraints['timeline_weeks']} weeks")
    
    # 2. Set up initial inputs for state machine
    # Read model name from command line args if provided, default to qwen
    model_name = sys.argv[1] if len(sys.argv) > 1 else "qwen2.5-coder:1.5b"
    print(f"  - Target LLM Engine: {model_name}")
    
    initial_state = {
        "pdf_path": "backend/papers/vlcd_paper.pdf",
        "constraints": user_constraints,
        "model_name": model_name
    }
    
    print(f"\n[Orchestrator Test] Invoking Full LangGraph Execution Flow on {model_name}...")
    final_state = graph.invoke(initial_state)
    
    # 3. Verify final report output
    report = final_state.get("report")
    loop_count = final_state.get("loop_count", 0)
    
    if report and report.markdown_content:
        output_path = "backend/papers/vlcd_adaptation_report_langgraph.md"
        
        # Save output Markdown string directly
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report.markdown_content)
            
        print("\n==================================================")
        print("         PIPELINE EXECUTION SUCCESSFUL!          ")
        print("==================================================")
        print(f"Total Refinement Loops Run: {loop_count}")
        print(f"Proposal Report Saved To: {output_path}")
        
        # Print a short preview of the resulting proposal report
        print("\nReport Preview (First 400 characters):")
        print("-" * 50)
        print(report.markdown_content[:400] + "...")
        print("-" * 50)
    else:
        print("\n[Error] Pipeline execution completed but returned an empty report.", file=sys.stderr)

if __name__ == "__main__":
    test_full_orchestration()
