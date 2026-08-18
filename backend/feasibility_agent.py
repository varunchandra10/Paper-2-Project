import os
import json
import sys
from typing import TypedDict
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END
from schemas import ComponentGraph, FeasibilityReport

class FeasibilityState(TypedDict):
    component_graph: ComponentGraph
    constraints: dict
    report: FeasibilityReport

def run_feasibility_agent(component_graph: ComponentGraph, constraints: dict, model_name: str = "qwen2.5-coder:1.5b") -> FeasibilityReport:
    """Uses Ollama structured output to validate project feasibility against hardware/timeline constraints."""
    
    # Initialize Ollama model with structured output
    llm = ChatOllama(model=model_name, temperature=0.0)
    structured_llm = llm.with_structured_output(FeasibilityReport)
    
    prompt = (
        "You are a senior Deep Learning Systems Optimization Engineer. Your task is to perform a feasibility analysis on the proposed research paper architecture "
        "and determine if it can be trained/fine-tuned within the user's specific hardware and project constraints.\n\n"
        "--- COMPONENT GRAPH ---\n"
        f"{json.dumps(component_graph.model_dump(), indent=2)}\n\n"
        "--- USER CONSTRAINTS ---\n"
        f"{json.dumps(constraints, indent=2)}\n\n"
        "Instructions:\n"
        "1. For each architectural component, evaluate its feasibility based on the user's available VRAM, GPU model, and dataset size. "
        "Consider if training or fine-tuning the component (e.g. Swin Transformer, CLIP Image Encoder, SFN) will fit in memory.\n"
        "2. Evaluate the training regime (batch size, epochs, learning rate, optimizer) feasibility. "
        "Estimate the training compute time based on the dataset size, epochs, and GPU model, and check if it fits the timeline (in weeks).\n"
        "3. Assign a status for each component and the training regime:\n"
        "   - 'FEASIBLE': Runs perfectly without issues.\n"
        "   - 'WARNING': Runs but might run out of memory (OOM), take too long, or require parameter-efficient optimization (e.g. freezing layers, LoRA, gradient accumulation).\n"
        "   - 'IMPOSSIBLE': Cannot run due to complete lack of hardware support (e.g. requires >24GB VRAM but user has 4GB VRAM).\n"
        "4. For any component marked with WARNING or IMPOSSIBLE, provide a concrete 'suggested_substitute' "
        "(e.g., 'Freeze Swin backbone and use SFN/adapter layers instead of full fine-tuning', 'Reduce batch size to 4 and use gradient accumulation', 'Substitute Swin Transformer with a lighter ResNet-18 or Swin-T backbone').\n"
        "5. Compile the findings into a list of actionable recommendations."
    )
    
    print("Sending request to local Ollama for feasibility validation...")
    report = structured_llm.invoke(prompt)
    return report

def feasibility_node(state: FeasibilityState) -> dict:
    component_graph = state["component_graph"]
    constraints = state["constraints"]
    report = run_feasibility_agent(component_graph, constraints)
    return {"report": report}

# Compile LangGraph Workflow
workflow = StateGraph(FeasibilityState)
workflow.add_node("feasibility", feasibility_node)
workflow.add_edge(START, "feasibility")
workflow.add_edge("feasibility", END)
graph = workflow.compile()
