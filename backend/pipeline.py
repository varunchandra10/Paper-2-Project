import os
import json
import sys
from typing import TypedDict, List
from langgraph.graph import StateGraph, START, END
from schemas import (
    PipelineOutput, PaperMetadata, ComponentGraph, FeasibilityReport, 
    BuildSequence, AdaptationReport, PaperDocument, ExtractedParameters, 
    GapReport, ResourceEstimationReport, ProjectSpecification, ProjectTree,
    StaticCheckReport, AutomatedTestReport, PaperCodeVerificationReport
)

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
    resource_estimation: ResourceEstimationReport  # Added for Day 24 resource estimation
    feasibility_report: FeasibilityReport
    build_sequence: BuildSequence
    project_specification: ProjectSpecification
    project_tree: ProjectTree
    static_check_report: StaticCheckReport
    automated_test_report: AutomatedTestReport
    code_verification_report: PaperCodeVerificationReport
    report: AdaptationReport





def run_refinement(component_graph: ComponentGraph, feasibility_report: FeasibilityReport) -> ComponentGraph:
    """Performs rule-based hyperparameter scaling and optimization when feasibility warning statuses occur."""
    print("\n[Refinement Node] Adjusting hyperparameters based on feasibility feedback...")
    from schemas import ParameterDetails

    # Check if modifications are needed
    if feasibility_report.overall_status in ["FEASIBLE_WITH_MODIFICATION", "NOT_FEASIBLE"]:
        print(f"  - Feasibility status is '{feasibility_report.overall_status}'. Applying hardware adaptation rules...")
        
        for comp in component_graph.components:
            # 1. Reduce Batch Size (batch size ↓)
            if "batch_size" in comp.parameters:
                orig = comp.parameters["batch_size"].value
                if orig != "4":
                    comp.parameters["batch_size"].value = "4"
                    comp.parameters["batch_size"].rationale = f"PAPER ORIGINAL: {orig} vs HARDWARE ADAPTATION: 4 (Reduced to fit local VRAM limits)."
                    comp.parameters["batch_size"].confidence = "ASSUMED"
                    print(f"      * Refined batch_size: {orig} -> 4")

            # 2. Reduce Image Size (image size ↓)
            if "input_size" in comp.parameters:
                orig = comp.parameters["input_size"].value
                if orig != "128x128" and orig != "128":
                    comp.parameters["input_size"].value = "128x128"
                    comp.parameters["input_size"].rationale = f"PAPER ORIGINAL: {orig} vs HARDWARE ADAPTATION: 128x128 (Reduced resolution to fit activation VRAM)."
                    comp.parameters["input_size"].confidence = "ASSUMED"
                    print(f"      * Refined input_size: {orig} -> 128x128")

            # 3. Model Variant Downsizing (model variant ↓)
            if "backbone" in comp.parameters:
                orig = comp.parameters["backbone"].value
                if "swin-b" in orig.lower() or "swin-large" in orig.lower():
                    comp.parameters["backbone"].value = "Swin-T"
                    comp.parameters["backbone"].rationale = f"PAPER ORIGINAL: {orig} vs HARDWARE ADAPTATION: Swin-T (Downgraded model complexity to fit weights memory)."
                    comp.parameters["backbone"].confidence = "ASSUMED"
                    print(f"      * Refined backbone: {orig} -> Swin-T")
                elif "resnet-50" in orig.lower() or "resnet50" in orig.lower():
                    comp.parameters["backbone"].value = "ResNet-18"
                    comp.parameters["backbone"].rationale = f"PAPER ORIGINAL: {orig} vs HARDWARE ADAPTATION: ResNet-18 (Downgraded model complexity to fit weights memory)."
                    comp.parameters["backbone"].confidence = "ASSUMED"
                    print(f"      * Refined backbone: {orig} -> ResNet-18")

            # 4. Increase Gradient Accumulation (gradient accumulation ↑)
            if "gradient_accumulation" in comp.parameters:
                orig = comp.parameters["gradient_accumulation"].value
                if orig != "4":
                    comp.parameters["gradient_accumulation"].value = "4"
                    comp.parameters["gradient_accumulation"].rationale = f"PAPER ORIGINAL: {orig} vs HARDWARE ADAPTATION: 4 (Increased accumulation steps to simulate original batch sizes)."
                    comp.parameters["gradient_accumulation"].confidence = "ASSUMED"
                    print(f"      * Refined gradient_accumulation: {orig} -> 4")
            else:
                if comp.type == "training":
                    comp.parameters["gradient_accumulation"] = ParameterDetails(
                        value="4",
                        confidence="ASSUMED",
                        rationale="PAPER ORIGINAL: 1 vs HARDWARE ADAPTATION: 4 (Increased accumulation steps to simulate original batch sizes)."
                    )
                    print("      * Refined gradient_accumulation: Added 4")

            # 5. Freeze Backbone Layers (freeze layers)
            if "freeze_backbone" in comp.parameters:
                orig = comp.parameters["freeze_backbone"].value
                if orig.lower() != "true":
                    comp.parameters["freeze_backbone"].value = "True"
                    comp.parameters["freeze_backbone"].rationale = f"PAPER ORIGINAL: {orig} vs HARDWARE ADAPTATION: True (Freeze backbone layers to reduce gradients VRAM footprint)."
                    comp.parameters["freeze_backbone"].confidence = "ASSUMED"
                    print(f"      * Refined freeze_backbone: {orig} -> True")
            else:
                if comp.type == "training":
                    comp.parameters["freeze_backbone"] = ParameterDetails(
                        value="True",
                        confidence="ASSUMED",
                        rationale="PAPER ORIGINAL: False vs HARDWARE ADAPTATION: True (Freeze backbone layers to reduce gradients VRAM footprint)."
                    )
                    print("      * Refined freeze_backbone: Added True")

            # 6. Enable Mixed Precision (use mixed precision)
            if "mixed_precision" in comp.parameters:
                orig = comp.parameters["mixed_precision"].value
                if orig.lower() != "fp16":
                    comp.parameters["mixed_precision"].value = "fp16"
                    comp.parameters["mixed_precision"].rationale = f"PAPER ORIGINAL: {orig} vs HARDWARE ADAPTATION: fp16 (Enabled FP16 training to save active training memory)."
                    comp.parameters["mixed_precision"].confidence = "ASSUMED"
                    print(f"      * Refined mixed_precision: {orig} -> fp16")
            else:
                if comp.type == "training":
                    comp.parameters["mixed_precision"] = ParameterDetails(
                        value="fp16",
                        confidence="ASSUMED",
                        rationale="PAPER ORIGINAL: fp32 vs HARDWARE ADAPTATION: fp16 (Enabled FP16 training to save active training memory)."
                    )
                    print("      * Refined mixed_precision: Added fp16")

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

def resource_estimation_node(state: PipelineState) -> dict:
    from core.hardware_profiler import profile_hardware
    from core.resource_estimator import estimate_resources
    print("\n[Orchestrator] Step 3.5: Running Resource Estimation Agent...")
    
    # 1. Profile system specs
    profile = profile_hardware()
    
    # 2. Estimate resources
    model = state.get("model_name", "qwen2.5-coder:1.5b")
    report = estimate_resources(state["extracted_parameters"], profile, model_name=model)
    return {"resource_estimation": report}

def feasibility_node(state: PipelineState) -> dict:
    from agents.feasibility_agent import run_feasibility_agent
    print("\n[Orchestrator] Step 4: Running Feasibility Agent...")
    model = state.get("model_name", "qwen2.5-coder:1.5b")
    feasibility_report = run_feasibility_agent(
        state["component_graph"], 
        state["constraints"], 
        state.get("resource_estimation"),
        model_name=model
    )
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
    metadata_dict = state["metadata"].model_dump() if hasattr(state["metadata"], "model_dump") else (state["metadata"].dict() if hasattr(state["metadata"], "dict") else state["metadata"])
    cg_dict = state["component_graph"].model_dump() if hasattr(state["component_graph"], "model_dump") else (state["component_graph"].dict() if hasattr(state["component_graph"], "dict") else state["component_graph"])
    pipeline_output = PipelineOutput(
        metadata=metadata_dict,
        component_graph=cg_dict
    )
    report = run_report_agent(pipeline_output, state["feasibility_report"], state["build_sequence"], model_name=model)
    return {"report": report}

def project_specification_node(state: PipelineState) -> dict:
    from agents.specification_agent import run_specification_agent
    print("\n[Orchestrator] Step 5.5: Running Project Specification Agent...")
    model = state.get("model_name", "qwen2.5-coder:1.5b")
    spec = run_specification_agent(
        state["component_graph"],
        state["feasibility_report"],
        state["build_sequence"],
        model_name=model
    )
    return {"project_specification": spec}

def file_planning_node(state: PipelineState) -> dict:
    from agents.file_planning_agent import run_file_planning_agent
    print("\n[Orchestrator] Step 5.6: Running File Planning Agent...")
    model = state.get("model_name", "qwen2.5-coder:1.5b")
    tree = run_file_planning_agent(
        state["project_specification"],
        model_name=model
    )
    return {"project_tree": tree}

def code_generation_node(state: PipelineState) -> dict:
    from agents.code_generation_agent import run_code_generation_agent
    
    spec = state["project_specification"]
    model = state.get("model_name", "qwen2.5-coder:1.5b")
    
    print("\n[Orchestrator] Step 5.7: Running Component-Level Code Generation...")
    
    # Establish target workspace folders
    PIPELINE_DIR = os.path.dirname(os.path.abspath(__file__))
    base_out_dir = os.path.join(PIPELINE_DIR, "generated_project")
    
    # 1. Mapped generation sequence
    generation_sequence = [
        ("dataset", "data/dataset.py"),
        ("backbone", "models/backbone.py"),
        ("fusion", "models/fusion.py"),
        ("decoder", "models/decoder.py"),
        ("loss", "training/loss.py"),
        ("trainer", "training/trainer.py"),
        ("evaluator", "evaluation/evaluator.py")
    ]
    
    # 2. Iterate and generate Python modules
    for comp_name, rel_path in generation_sequence:
        out_filepath = os.path.join(base_out_dir, rel_path.replace("/", os.sep))
        os.makedirs(os.path.dirname(out_filepath), exist_ok=True)
        
        # Run code generation agent
        code = run_code_generation_agent(comp_name, rel_path, spec, model_name=model)
        
        # Save to disk
        with open(out_filepath, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"  [OK] Successfully wrote code file: {rel_path}")
        
    # 3. Write ancillary files (config.json, requirements.txt, README.md)
    config_path = os.path.join(base_out_dir, "configs", "config.json")
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump({
            "model_name": spec.components[0] if (spec.components and isinstance(spec.components, list)) else "VisualEncoder",
            "batch_size": 4,
            "gradient_accumulation": 4,
            "mixed_precision": "fp16",
            "learning_rate": 0.0001
        }, f, indent=2)
    print("  [OK] Successfully wrote config file: configs/config.json")
    
    req_path = os.path.join(base_out_dir, "requirements.txt")
    with open(req_path, "w", encoding="utf-8") as f:
        f.write("torch>=2.0.0\ntorchvision\nnumpy\npsutil\nscikit-learn\nscikit-image\npillow\n")
    print("  [OK] Successfully wrote dependency file: requirements.txt")
    
    readme_path = os.path.join(base_out_dir, "README.md")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(f"# Unified Adaptations Project\n\n## Architecture Blueprint\n{spec.architecture}\n\n## Requirements\n{spec.requirements}\n")
    print("  [OK] Successfully wrote documentation file: README.md")
    
    return {}

def static_check_node(state: PipelineState) -> dict:
    from core.static_checker import run_static_checks
    print("\n[Orchestrator] Step 5.8: Running Static Verification Checks...")
    
    PIPELINE_DIR = os.path.dirname(os.path.abspath(__file__))
    base_out_dir = os.path.join(PIPELINE_DIR, "generated_project")
    
    report = run_static_checks(base_out_dir)
    print(f"  [OK] Static Checks Result: Syntax Valid={report.syntax_valid}, Imports Valid={report.imports_valid}, Dependencies Valid={report.dependencies_valid}")
    if report.errors:
        for err in report.errors:
            print(f"    - {err}")
            
    return {"static_check_report": report}

def automated_test_node(state: PipelineState) -> dict:
    from core.test_runner import run_automated_tests
    print("\n[Orchestrator] Step 5.9: Running Automated Testing Checks...")
    
    PIPELINE_DIR = os.path.dirname(os.path.abspath(__file__))
    base_out_dir = os.path.join(PIPELINE_DIR, "generated_project")
    
    report = run_automated_tests(base_out_dir)
    print(f"  [OK] Automated Tests Result: Dataset={report.dataset_check}, Backbone={report.backbone_check}, Fusion={report.fusion_check}, Decoder={report.decoder_check}, Loss={report.loss_check}")
    if report.details:
        for log in report.details:
            print(f"    {log}")
            
    return {"automated_test_report": report}

def code_verification_node(state: PipelineState) -> dict:
    from core.paper_code_verifier import run_paper_code_verification
    print("\n[Orchestrator] Step 5.10: Running Paper-to-Code Parameter Checks...")
    
    PIPELINE_DIR = os.path.dirname(os.path.abspath(__file__))
    base_out_dir = os.path.join(PIPELINE_DIR, "generated_project")
    
    report = run_paper_code_verification(base_out_dir, state.get("extracted_parameters"))
    print(f"  [OK] Verification Report Generated successfully with {len(report.comparisons)} checks.")
    for comp in report.comparisons:
        print(f"    {comp}")
        
    return {"code_verification_report": report}







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
workflow.add_node("resource_estimation", resource_estimation_node)
workflow.add_node("feasibility", feasibility_node)
workflow.add_node("refinement", refinement_node)
workflow.add_node("sequencing", sequencing_node)
workflow.add_node("project_specification", project_specification_node)
workflow.add_node("file_planning", file_planning_node)
workflow.add_node("code_generation", code_generation_node)
workflow.add_node("static_check", static_check_node)
workflow.add_node("automated_test", automated_test_node)
workflow.add_node("code_verification", code_verification_node)
workflow.add_node("report", report_node)




# Set up edges
workflow.add_edge(START, "ingestion")
workflow.add_edge("ingestion", "decomposition")
workflow.add_edge("decomposition", "parameter_extraction")
workflow.add_edge("parameter_extraction", "gap_finding")
workflow.add_edge("gap_finding", "resource_estimation")
workflow.add_edge("resource_estimation", "feasibility")

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

workflow.add_edge("sequencing", "project_specification")
workflow.add_edge("project_specification", "file_planning")
workflow.add_edge("file_planning", "code_generation")
workflow.add_edge("code_generation", "static_check")
workflow.add_edge("static_check", "automated_test")
workflow.add_edge("automated_test", "code_verification")
workflow.add_edge("code_verification", "report")
workflow.add_edge("report", END)

# Compile pipeline orchestrator graph
graph = workflow.compile()
