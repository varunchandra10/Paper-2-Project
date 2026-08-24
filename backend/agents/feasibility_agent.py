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
    
    # num_predict caps the token output to prevent the model looping forever on long 'reason' fields
    llm = ChatOllama(model=model_name, temperature=0.0, num_ctx=4096, num_predict=1024)
    structured_llm = llm.with_structured_output(FeasibilityReport)
    
    # Keep the component graph summary brief to reduce prompt length
    comp_summary = [
        {"name": c.name, "type": c.type, "description": c.description[:120]}
        for c in component_graph.components
    ]
    
    prompt = (
        "You are a senior Deep Learning Systems Optimization Engineer. Perform a feasibility analysis "
        "on the proposed architecture given the user hardware constraints.\n\n"
        "--- COMPONENT SUMMARY ---\n"
        f"{json.dumps(comp_summary, indent=2)}\n\n"
        "--- USER CONSTRAINTS ---\n"
        f"{json.dumps(constraints, indent=2)}\n\n"
        "STRICT RULES:\n"
        "- For each component: status ('FEASIBLE'/'WARNING'/'IMPOSSIBLE'), reason (1 sentence max), "
        "suggested_substitute (1 concrete action max 20 words).\n"
        "- Do NOT repeat yourself. Each field must be concise.\n"
        "- training_status: 'FEASIBLE'/'WARNING'/'IMPOSSIBLE'\n"
        "- training_reason: 1 sentence about timeline/epoch compute.\n"
        "- training_substitute: 1 actionable suggestion.\n"
        "- recommendations: 3-5 bullet strings.\n"
        "- alternatives: 2 platforms (Google Colab, Kaggle) with brief setup steps.\n"
        "- overall_status: aggregate status across all components."
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
                    reason="Backbone parameters may exceed desktop VRAM budget.",
                    suggested_substitute="Freeze backbone layers and use LoRA fine-tuning."
                ) for comp in component_graph.components
            ],
            training_status="WARNING",
            training_reason="Training epochs are high for local GPU limitations.",
            training_substitute="Reduce batch size and implement gradient accumulation steps.",
            recommendations=[
                "Freeze backbones and train only adapter layers.",
                "Use gradient accumulation to simulate larger batch sizes.",
                "Monitor VRAM usage per epoch."
            ],
            alternatives=[
                AlternativePlatform(
                    platform_name="Google Colab",
                    description="Free NVIDIA T4 GPU (~15GB VRAM).",
                    how_to_use="Set runtime to GPU T4, clone repo, run training script."
                ),
                AlternativePlatform(
                    platform_name="Kaggle Kernels",
                    description="30 free GPU hours/week with dual T4.",
                    how_to_use="Enable GPU accelerator, import dataset, run pipeline."
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
