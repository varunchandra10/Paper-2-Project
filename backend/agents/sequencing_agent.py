import os
import json
import sys
from typing import TypedDict
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END
from schemas import ComponentGraph, FeasibilityReport, BuildSequence

class SequencingState(TypedDict):
    component_graph: ComponentGraph
    feasibility_report: FeasibilityReport
    build_sequence: BuildSequence

def run_sequencing_agent(component_graph: ComponentGraph, feasibility_report: FeasibilityReport, model_name: str = "qwen2.5-coder:1.5b") -> BuildSequence:
    """Uses Ollama structured output to convert feasibility-adjusted graph into dependency-ordered milestones."""
    
    # Initialize Ollama model with structured output
    llm = ChatOllama(model=model_name, temperature=0.0, num_ctx=4096)
    structured_llm = llm.with_structured_output(BuildSequence)
    
    prompt = (
        "You are a Principal AI Architect and Project Manager. Your task is to analyze the Component Graph and the Feasibility Report "
        "and convert them into a structured, dependency-ordered engineering build plan (a Build Sequence).\n\n"
        "--- COMPONENT GRAPH ---\n"
        f"{json.dumps(component_graph.model_dump(), indent=2)}\n\n"
        "--- FEASIBILITY REPORT ---\n"
        f"{json.dumps(feasibility_report.model_dump(), indent=2)}\n\n"
        "Instructions:\n"
        "1. Define a series of build milestones (id: 1, 2, 3, etc.) representing the step-by-step implementation sequence of the project.\n"
        "2. CRITICAL PRINCIPLE: Cheap, quick validation steps MUST always precede compute-heavy or risky steps. For example:\n"
        "   - Setting up data parsing and PyTorch dataset loaders is Step 1 (Low complexity, easy validation).\n"
        "   - Testing loss functions, evaluation metrics, and setting up model checkpoints is Step 2.\n"
        "   - Loading and verifying pre-trained frozen backbones (like RemoteCLIP / Swin-T) is Step 3.\n"
        "   - Building and integrating small, adapter layers (like SFN / Bridging Module) is Step 4.\n"
        "   - Training/fine-tuning model decoders and training runs with scaled epochs/batches is Step 5 (High complexity, high compute).\n"
        "3. For each milestone, provide the name, core objectives, components involved, estimated complexity, and a detailed dependency rationale "
        "explaining why it is sequenced at this specific point."
    )
    
    print("Sending request to local Ollama for build sequencing...")
    try:
        sequence = structured_llm.invoke(prompt)
    except Exception as e:
        print(f"Warning: Sequencing agent LLM call failed ({e}). Returning baseline milestones sequence.")
        from schemas import Milestone
        sequence = BuildSequence(
            milestones=[
                Milestone(
                    id=1,
                    name="Environment Setup & Data Pipeline Validation",
                    objectives=["Prepare python environment.", "Validate PDF parser and JSON structure extraction.", "Construct PyTorch custom Dataset loader."],
                    components_involved=[comp.name for comp in component_graph.components[:1]] if component_graph.components else ["Swin Transformer (RFN)"],
                    estimated_complexity="LOW",
                    dependency_rationale="We must establish data ingestion pipelines and environment structures before assembling deep architectures."
                ),
                Milestone(
                    id=2,
                    name="Backbone Loaders & Feature Extraction Verification",
                    objectives=["Load pre-trained frozen backbones.", "Test embedding dimension mapping.", "Validate feature shapes from Swin backbone."],
                    components_involved=[comp.name for comp in component_graph.components[:2]] if len(component_graph.components) >= 2 else ["Swin Transformer (RFN)", "RemoteCLIP Image Encoder"],
                    estimated_complexity="MEDIUM",
                    dependency_rationale="Verifying shape compatibility of static backbone layers prevents compilation issues downstream."
                ),
                Milestone(
                    id=3,
                    name="Adapter Layers Integration & Forward Pass Validation",
                    objectives=["Build Side Fusion Network (SFN) adapter layer.", "Conduct standard forward pass checks.", "Verify attention alignment."],
                    components_involved=[comp.name for comp in component_graph.components[2:3]] if len(component_graph.components) >= 3 else ["Side Fusion Network (SFN)"],
                    estimated_complexity="MEDIUM",
                    dependency_rationale="Small adapter layers must be verified via a standard forward pass before setting up complex training procedures."
                ),
                Milestone(
                    id=4,
                    name="Loss Functions & Training Pipeline Compilations",
                    objectives=["Construct loss functions.", "Test gradient update updates.", "Implement local checkpointer hooks."],
                    components_involved=["Loss functions"],
                    estimated_complexity="LOW",
                    dependency_rationale="Validation of local gradient steps guarantees that the training process does not run out of memory or raise shape errors."
                ),
                Milestone(
                    id=5,
                    name="Scaled Training & Model Synthesis Profile",
                    objectives=["Execute training epochs using local parameter limits.", "Verify convergence metrics.", "Generate final reports."],
                    components_involved=[comp.name for comp in component_graph.components[-1:]] if component_graph.components else ["Swin Transformer Decoder"],
                    estimated_complexity="HIGH",
                    dependency_rationale="Scaled epochs and decoder optimizations represent the final and most compute-heavy step in implementation."
                )
            ]
        )
    return sequence

def sequencing_node(state: SequencingState) -> dict:
    component_graph = state["component_graph"]
    feasibility_report = state["feasibility_report"]
    build_sequence = run_sequencing_agent(component_graph, feasibility_report)
    return {"build_sequence": build_sequence}

# Compile LangGraph Workflow
workflow = StateGraph(SequencingState)
workflow.add_node("sequencing", sequencing_node)
workflow.add_edge(START, "sequencing")
workflow.add_edge("sequencing", END)
graph = workflow.compile()
