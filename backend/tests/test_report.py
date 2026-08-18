import os
import json
import sys

# Add parent directory to path to allow importing from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from schemas import PipelineOutput, FeasibilityReport, BuildSequence
from agents.report_agent import graph

def test_report():
    input_pipeline_path = "backend/papers/vlcd_full_pipeline_output.json"
    input_feasibility_path = "backend/papers/vlcd_feasibility_report.json"
    input_sequence_path = "backend/papers/vlcd_build_sequence.json"
    
    # Check that previous JSONs exist
    paths = [input_pipeline_path, input_feasibility_path, input_sequence_path]
    if any(not os.path.exists(p) for p in paths):
        print("Error: Previous JSON results missing. Please run all previous stages first.", file=sys.stderr)
        sys.exit(1)

    print("Loading previous artifacts...")
    with open(input_pipeline_path, "r", encoding="utf-8") as f:
        pipeline_data = json.load(f)
    with open(input_feasibility_path, "r", encoding="utf-8") as f:
        feasibility_data = json.load(f)
    with open(input_sequence_path, "r", encoding="utf-8") as f:
        sequence_data = json.load(f)
        
    pipeline_output = PipelineOutput(**pipeline_data)
    feasibility_report = FeasibilityReport(**feasibility_data)
    build_sequence = BuildSequence(**sequence_data)

    print("\nInvoking LangGraph Adaptation Report Agent flow...")
    initial_state = {
        "pipeline_output": pipeline_output,
        "feasibility_report": feasibility_report,
        "build_sequence": build_sequence
    }
    
    # Run graph
    result = graph.invoke(initial_state)
    report_output = result.get("report")

    if report_output and report_output.markdown_content:
        output_path = "backend/papers/vlcd_adaptation_report.md"
        
        # Save output Markdown string directly
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(report_output.markdown_content)
            
        print("\n=== ADAPTATION REPORT SYNTHESIS COMPLETE ===")
        print(f"Successfully generated proposal report!")
        print(f"File saved to: {output_path}")
        print("\nReport Preview (First 500 characters):")
        print("-" * 50)
        print(report_output.markdown_content[:500] + "...")
        print("-" * 50)
    else:
        print("Error: Adaptation report returned empty output.", file=sys.stderr)

if __name__ == "__main__":
    test_report()
