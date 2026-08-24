import os
import json
import sys
from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from schemas import PipelineOutput, PaperMetadata, ComponentGraph, FeasibilityReport, BuildSequence, AdaptationReport, PaperDocument, ExtractedParameters, GapReport

# Define unified pipeline state
class PipelineState(TypedDict):
    pdf_path: str
    constraints: dict
    model_name: str  # Added to allow dynamic model swapping
    loop_count: int
    raw_sections: dict
    metadata: PaperMetadata
    paper_doc: PaperDocument  # Added for Phase 5 canonical tracking
    component_graph: ComponentGraph
    extracted_parameters: ExtractedParameters  # Added for Day 21 parameter extraction
    gap_report: GapReport  # Added for Day 22 parameter gap classification
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
    from extraction import route_and_extract, merge_extractions
    from retrieval import chunk_paper_document, generate_local_embedding, PaperVectorDB
    from agents.ingestion_agent import run_ingestion_agent
    
    pdf_path = state["pdf_path"]
    print(f"\n[Orchestrator] Step 1: Parsing and merging paper '{pdf_path}'...")
    
    # 1. Routing & extraction parsing -> Merge to canonical PaperDocument
    routed_result = route_and_extract(pdf_path)
    paper_doc = merge_extractions(routed_result)
    
    # 2. Slice and insert layout chunks into PostgreSQL + pgvector
    print("[Orchestrator] Slicing document and saving embeddings in pgvector database...")
    chunks = chunk_paper_document(paper_doc)
    embeddings = [generate_local_embedding(c.content) for c in chunks]
    
    db = PaperVectorDB()
    db.initialize_db()
    db.insert_paper_document(paper_doc, chunks, embeddings)
    
    # 3. Compile parsed sections from PaperDocument
    parsed_sections = {sec.title: sec.content for sec in paper_doc.sections}
    parsed_sections["Metadata / Front Matter"] = f"Title: {paper_doc.metadata.title}\nAbstract: {paper_doc.metadata.abstract}"
    
    model = state.get("model_name", "qwen2.5-coder:1.5b")
    metadata = run_ingestion_agent(parsed_sections, model_name=model)
    return {
        "raw_sections": parsed_sections, 
        "metadata": metadata, 
        "paper_doc": paper_doc, 
        "loop_count": 0
    }

def decomposition_node(state: PipelineState) -> dict:
    from agents.decomposition_agent import run_decomposition_agent
    print("\n[Orchestrator] Step 2: Running Method Decomposition Agent...")
    model = state.get("model_name", "qwen2.5-coder:1.5b")
    component_graph = run_decomposition_agent(
        state["raw_sections"], 
        model_name=model, 
        paper_doc=state["paper_doc"]
    )
    return {"component_graph": component_graph}

def parameter_extraction_node(state: PipelineState) -> dict:
    from agents.parameter_agent import run_parameter_agent
    print("\n[Orchestrator] Step 2.5: Running Parameter Extraction Agent...")
    model = state.get("model_name", "qwen2.5-coder:1.5b")
    extracted_parameters = run_parameter_agent(state["paper_doc"], model_name=model)
    return {"extracted_parameters": extracted_parameters}

def gap_finding_node(state: PipelineState) -> dict:
    from agents.gap_agent import run_gap_agent
    print("\n[Orchestrator] Step 3: Running Gap-Finding Agent...")
    model = state.get("model_name", "qwen2.5-coder:1.5b")
    gap_report = run_gap_agent(state["component_graph"], state["extracted_parameters"], model_name=model)
    return {"gap_report": gap_report, "component_graph": state["component_graph"]}

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
workflow.add_node("parameter_extraction", parameter_extraction_node)
workflow.add_node("gap_finding", gap_finding_node)
workflow.add_node("feasibility", feasibility_node)
workflow.add_node("refinement", refinement_node)
workflow.add_node("sequencing", sequencing_node)
workflow.add_node("report", report_node)

# Set up edges
workflow.add_edge(START, "ingestion")
workflow.add_edge("ingestion", "decomposition")
workflow.add_edge("decomposition", "parameter_extraction")
workflow.add_edge("parameter_extraction", "gap_finding")
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
