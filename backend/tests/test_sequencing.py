import os
import json
import sys

# Add parent directory to path to allow importing from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from schemas import PipelineOutput, FeasibilityReport
from agents.sequencing_agent import graph

def test_sequencing():
    input_pipeline_path = "backend/papers/vlcd_full_pipeline_output.json"
    input_feasibility_path = "backend/papers/vlcd_feasibility_report.json"
    
    if not os.path.exists(input_pipeline_path) or not os.path.exists(input_feasibility_path):
        print("Error: Previous JSON results not found. Please run pipeline and feasibility tests first.", file=sys.stderr)
        sys.exit(1)

    print("Loading previous pipeline output and feasibility report...")
    with open(input_pipeline_path, "r", encoding="utf-8") as f:
        pipeline_data = json.load(f)
    with open(input_feasibility_path, "r", encoding="utf-8") as f:
        feasibility_data = json.load(f)
        
    pipeline_output = PipelineOutput(**pipeline_data)
    component_graph = pipeline_output.component_graph
    feasibility_report = FeasibilityReport(**feasibility_data)

    print("\nInvoking LangGraph Build Sequencing Agent flow...")
    initial_state = {
        "component_graph": component_graph,
        "feasibility_report": feasibility_report
    }
    
    # Run graph
    result = graph.invoke(initial_state)
    build_sequence = result.get("build_sequence")

    if build_sequence:
        output_path = "backend/papers/vlcd_build_sequence.json"
        
        # Save output structured Pydantic model
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(build_sequence.model_dump(), f, indent=4, ensure_ascii=False)
            
        print("\n=== BUILD SEQUENCING COMPLETE ===")
        print(f"Total Milestones Scheduled: {len(build_sequence.milestones)}")
        
        for milestone in build_sequence.milestones:
            print(f"\n[{milestone.id}] Milestone: {milestone.name}")
            print(f"    - Complexity: {milestone.estimated_complexity}")
            print(f"    - Components: {', '.join(milestone.components_involved)}")
            print(f"    - Dependency Rationale: {milestone.dependency_rationale}")
            print(f"    - Core Tasks/Objectives:")
            for task in milestone.objectives:
                print(f"        * {task}")
                
        print(f"\nSaved build sequence JSON to: {output_path}")
    else:
        print("Error: Build sequencing returned empty sequence.", file=sys.stderr)

if __name__ == "__main__":
    test_sequencing()
