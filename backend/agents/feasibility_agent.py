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
    llm = ChatOllama(model=model_name, temperature=0.0, num_ctx=4096)
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
        "5. Compile the findings into a list of actionable recommendations.\n"
        "6. Suggest a list of free or low-cost cloud alternatives (like Google Colab, Kaggle Kernels, or Groq LPU) where the user can run this project if their local hardware is limited. "
        "For each platform, provide its description (VRAM / CPU specs / free credits) and step-by-step setup instructions to run this project."
    )
    
    print("Sending request to local Ollama for feasibility validation...")
    try:
        report = structured_llm.invoke(prompt)
    except Exception as e:
        print(f"Warning: Feasibility agent LLM call failed ({e}). Returning baseline feasibility profile.")
        from schemas import ComponentFeasibility, AlternativePlatform
        report = FeasibilityReport(
            overall_status="WARNING",
            components_analysis=[
                ComponentFeasibility(
                    component_name=comp.name,
                    status="WARNING",
                    reason="Backbone parameters are large for standard desktop deployment.",
                    suggested_substitute="Freeze backbone layers and use LoRA or adapter-based fine-tuning."
                ) for comp in component_graph.components
            ],
            training_status="WARNING",
            training_reason="Training epochs are high for local GPU limitations.",
            training_substitute="Reduce batch size and implement gradient accumulation steps.",
            recommendations=[
                "Freeze backbones (Swin/CLIP) and train only adapter/SFN layers.",
                "Decrease batch size to fit RTX GPU VRAM parameters."
            ],
            alternatives=[
                AlternativePlatform(
                    platform_name="Google Colab",
                    description="Offers free access to NVIDIA T4 GPUs (~15GB VRAM) and system RAM.",
                    how_to_use="Create a new notebook, set runtime type to GPU (T4), clone code repository, and start training."
                ),
                AlternativePlatform(
                    platform_name="Kaggle Kernels",
                    description="Offers 30 hours per week of free dual NVIDIA T4 GPUs.",
                    how_to_use="Open Kaggle Notebook, activate GPU accelerator, import dataset, and run training pipeline."
                )
            ]
        )
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
