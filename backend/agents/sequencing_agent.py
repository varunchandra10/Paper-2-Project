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
    llm = ChatOllama(model=model_name, temperature=0.0)
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
    sequence = structured_llm.invoke(prompt)
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
