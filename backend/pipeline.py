import os
import json
import sys
from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from schemas import PipelineOutput, PaperMetadata, ComponentGraph, FeasibilityReport, BuildSequence, AdaptationReport

# Define unified pipeline state
class PipelineState(TypedDict):
    pdf_path: str
    constraints: dict
    model_name: str  # Added to allow dynamic model swapping
    loop_count: int
    raw_sections: dict
    metadata: PaperMetadata
    component_graph: ComponentGraph
    feasibility_report: FeasibilityReport
    build_sequence: BuildSequence
    report: AdaptationReport

def run_refinement(component_graph: ComponentGraph, feasibility_report: FeasibilityReport) -> ComponentGraph:
    """Performs rule-based hyperparameter scaling and optimization when feasibility warnings occur."""
    print("\n[Refinement Node] Adjusting hyperparameters based on feasibility feedback...")
    
    # 1. Look for Visual Backbone bottlenecks (OOM issues)
    for comp in component_graph.components:
        if comp.type == "encoder" and "backbone" in comp.name.lower():
            # If the backbone is too large, adjust patch size or parameters
            if "patch_size" in comp.parameters:
                print(f"  - Visual Backbone ('{comp.name}'): Optimizing patch_size to 4 for memory alignment.")
                comp.parameters["patch_size"].value = "4"
                comp.parameters["patch_size"].rationale = "Auto-adjusted from 16 to 4 to reduce transformer patch sequence length"
                comp.parameters["patch_size"].confidence = "ASSUMED"
                
    # 2. Look for training regime timelines/batch bottlenecks
    if feasibility_report.training_status in ["WARNING", "IMPOSSIBLE"]:
        print(f"  - Training Regime: Scaling parameters according to feedback: '{feasibility_report.training_substitute}'")
        for comp in component_graph.components:
            if comp.type in ["training", "optimizer", "regime"] or "optimizer" in comp.name.lower():
                if "batch_size" in comp.parameters:
                    print("      * Reducing training batch_size from 24 to 4 to fit in 8GB VRAM.")
                    comp.parameters["batch_size"].value = "4"
                    comp.parameters["batch_size"].rationale = "Reduced to 4 to prevent local Out-Of-Memory (OOM) error"
                    comp.parameters["batch_size"].confidence = "ASSUMED"
                if "epochs" in comp.parameters:
                    print("      * Reducing epochs from 250 to 50 to complete within the 2-week limit.")
                    comp.parameters["epochs"].value = "50"
                    comp.parameters["epochs"].rationale = "Scaled down to fit project timeline budget"
                    comp.parameters["epochs"].confidence = "ASSUMED"
                    
    return component_graph

# --- Node Definitions ---

def ingestion_node(state: PipelineState) -> dict:
    from agents.ingestion_agent import run_ingestion_agent
    from parser import parse_pdf
    
    pdf_path = state["pdf_path"]
    parsed_path = pdf_path.replace(".pdf", "_parsed.json")
    
    if not os.path.exists(parsed_path):
        print(f"\n[Orchestrator] Step 1: Parsed sections JSON not found. Running parser on '{pdf_path}'...")
        parsed_sections = parse_pdf(pdf_path)
        if parsed_sections:
            with open(parsed_path, "w", encoding="utf-8") as f:
                json.dump(parsed_sections, f, indent=4, ensure_ascii=False)
            print(f"[Orchestrator] Saved parsed sections to '{parsed_path}'")
        else:
            raise FileNotFoundError(f"Failed to parse PDF at '{pdf_path}'")
    else:
        print(f"\n[Orchestrator] Step 1: Loading existing parsed sections from '{parsed_path}'...")
        with open(parsed_path, "r", encoding="utf-8") as f:
            parsed_sections = json.load(f)
    
    model = state.get("model_name", "qwen2.5-coder:1.5b")
    metadata = run_ingestion_agent(parsed_sections, model_name=model)
    return {"raw_sections": parsed_sections, "metadata": metadata, "loop_count": 0}

def decomposition_node(state: PipelineState) -> dict:
    from agents.decomposition_agent import run_decomposition_agent
    print("\n[Orchestrator] Step 2: Running Method Decomposition Agent...")
    model = state.get("model_name", "qwen2.5-coder:1.5b")
    component_graph = run_decomposition_agent(state["raw_sections"], model_name=model)
    return {"component_graph": component_graph}

def gap_finding_node(state: PipelineState) -> dict:
    from agents.gap_agent import run_gap_agent
    print("\n[Orchestrator] Step 3: Running Gap-Finding Agent...")
    model = state.get("model_name", "qwen2.5-coder:1.5b")
    gap_filled_graph = run_gap_agent(state["component_graph"], model_name=model)
    return {"component_graph": gap_filled_graph}

def feasibility_node(state: PipelineState) -> dict:
    from agents.feasibility_agent import run_feasibility_agent
    print("\n[Orchestrator] Step 4: Running Feasibility Agent...")
    model = state.get("model_name", "qwen2.5-coder:1.5b")
    feasibility_report = run_feasibility_agent(state["component_graph"], state["constraints"], model_name=model)
    return {"feasibility_report": feasibility_report}

def refinement_node(state: PipelineState) -> dict:
    refined_graph = run_refinement(state["component_graph"], state["feasibility_report"])
    return {"component_graph": refined_graph, "loop_count": state["loop_count"] + 1}

def sequencing_node(state: PipelineState) -> dict:
    from agents.sequencing_agent import run_sequencing_agent
    print("\n[Orchestrator] Step 5: Running Build Sequencing Agent...")
    model = state.get("model_name", "qwen2.5-coder:1.5b")
    build_sequence = run_sequencing_agent(state["component_graph"], state["feasibility_report"], model_name=model)
    return {"build_sequence": build_sequence}

def report_node(state: PipelineState) -> dict:
    from agents.report_agent import run_report_agent
    print("\n[Orchestrator] Step 6: Running Adaptation Report Agent...")
    model = state.get("model_name", "qwen2.5-coder:1.5b")
    pipeline_output = PipelineOutput(
        metadata=state["metadata"],
        component_graph=state["component_graph"]
    )
    report = run_report_agent(pipeline_output, state["feasibility_report"], state["build_sequence"], model_name=model)
    return {"report": report}

# --- Routing Logic ---

def route_after_feasibility(state: PipelineState) -> str:
    """Routes state based on feasibility status and loop counts."""
    # Loop at most once for refinement. If feasible, skip refinement.
    if state["feasibility_report"].overall_status == "FEASIBLE" or state.get("loop_count", 0) >= 1:
        print("\n[Router] Feasibility check passed (or refinement loop count limit reached). Proceeding to sequencing.")
        return "sequencing"
    else:
        print(f"\n[Router] Feasibility warning: '{state['feasibility_report'].overall_status}'. Routing to Refinement Node.")
        return "refinement"

# --- Assemble the LangGraph workflow ---
workflow = StateGraph(PipelineState)

# Add all agent nodes
workflow.add_node("ingestion", ingestion_node)
workflow.add_node("decomposition", decomposition_node)
workflow.add_node("gap_finding", gap_finding_node)
workflow.add_node("feasibility", feasibility_node)
workflow.add_node("refinement", refinement_node)
workflow.add_node("sequencing", sequencing_node)
workflow.add_node("report", report_node)

# Set up edges
workflow.add_edge(START, "ingestion")
workflow.add_edge("ingestion", "decomposition")
workflow.add_edge("decomposition", "gap_finding")
workflow.add_edge("gap_finding", "feasibility")

# Conditional loop edge after feasibility validation
workflow.add_conditional_edges(
    "feasibility",
    route_after_feasibility,
    {
        "refinement": "refinement",
        "sequencing": "sequencing"
    }
)

# Route back to feasibility check after refining
workflow.add_edge("refinement", "feasibility")

workflow.add_edge("sequencing", "report")
workflow.add_edge("report", END)

# Compile pipeline orchestrator graph
graph = workflow.compile()
