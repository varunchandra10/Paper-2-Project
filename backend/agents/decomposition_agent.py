import os
import json
import sys
from typing import List, Dict, TypedDict
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END
from schemas import Component, ComponentGraph

# Define LangGraph State
class AgentState(TypedDict):
    parsed_sections: dict
    component_graph: ComponentGraph

def run_decomposition_agent(parsed_sections: dict, model_name: str = "qwen2.5-coder:1.5b") -> ComponentGraph:
    """Uses Ollama structured output to extract the architectural component graph from Method & Experiments sections."""
    
    # Extract the Method section content
    method_content = parsed_sections.get("III. METHOD", "")
    if not method_content:
        for key in parsed_sections.keys():
            if "method" in key.lower():
                method_content = parsed_sections[key]
                break

    # Extract Experiments section content for training hyperparameters (learning rates, batch size, etc.)
    experiments_content = parsed_sections.get("IV. EXPERIMENTS", "")
    if not experiments_content:
        for key in parsed_sections.keys():
            if "experiment" in key.lower():
                experiments_content = parsed_sections[key]
                break

    # Truncate Experiments section to only keep subsection A (Implementation Details)
    # This removes redundant evaluation metrics and dataset descriptions, saving context tokens
    if experiments_content:
        cutoff = experiments_content.find("B. Evaluation")
        if cutoff == -1:
            cutoff = experiments_content.find("B. ")
        if cutoff != -1:
            experiments_content = experiments_content[:cutoff]

    if not method_content:
        print("Warning: Method section not found. Falling back to using first available section for decomposition.")
        # Fall back to first available non-empty section
        for key, content in parsed_sections.items():
            if content.strip():
                method_content = content
                break
                
    # Initialize Ollama model with structured output
    print(f"Initializing ChatOllama with model '{model_name}'...")
    llm = ChatOllama(model=model_name, temperature=0.0)
    structured_llm = llm.with_structured_output(ComponentGraph)

    # Prompt instructing the LLM
    prompt = (
        "You are an expert machine learning architect. Your task is to analyze the METHOD and EXPERIMENTS sections of a research paper "
        "and decompose its architecture into its specific, named sub-components (a component graph).\n\n"
        f"--- METHOD SECTION CONTENT ---\n{method_content}\n\n"
        f"--- EXPERIMENTS SECTION CONTENT ---\n{experiments_content}\n\n"
        "Instructions:\n"
        "1. Identify and extract each specific, named sub-component defined in the paper. "
        "Do NOT group them into generic category names (like 'Encoder' or 'Fusion'). Instead, extract specific components "
        "such as 'Swin Transformer (RFN)', 'RemoteCLIP / CLIP Image Encoder', 'Side Fusion Network (SFN)', 'Bridging Module', 'Context Optimization (CoOp)', 'Change Feature Calculation (CFC) module', 'Swin Transformer Decoder', 'Cross-Entropy Loss', 'Optimizer', etc.\n\n"
        "2. Categorize each component's 'type' field as one of:\n"
        "- 'encoder' (e.g., visual backbones, text encoders)\n"
        "- 'fusion' (e.g., cross-attention, feature fusion modules, bridging modules, context decoders)\n"
        "- 'decoder' (e.g., segmentation decoders, mask heads)\n"
        "- 'loss' (e.g., custom losses, cross-entropy)\n"
        "- 'training' (e.g., optimizer, learning rate scheduler, training steps)\n\n"
        "3. For each component, extract its specific paper-defined name, description, inputs, outputs, and its parameters.\n\n"
        "For each parameter, extract: \n"
        "- 'value': The concrete value/number (e.g., '24', '0.001', '512', or 'Not specified' if not found in the text).\n"
        "- 'confidence': 'CONFIRMED' if the value is explicitly stated in the text. Use 'ASSUMED' if the value is not explicitly stated (and you had to set it to 'Not specified' or use standard defaults).\n"
        "- 'rationale': A brief explanation of how you found the value or why it is marked as 'Not specified'.\n\n"
        "CRITICAL WARNING:\n"
        "- Extract only CONCRETE values and numbers mentioned in the text (e.g., batch_size: '24', learning_rate: '0.001', epochs: '250', width: '512').\n"
        "- Do NOT use template variables or placeholders like '{batch_size}', '{learning_rate}', or '{width}'.\n"
        "- If a hyperparameter value is not mentioned in the text, use 'Not specified' and set confidence to 'ASSUMED', but NEVER generate curly-brace placeholders."
    )

    try:
        print("Sending request to local Ollama for structured method decomposition...")
        component_graph = structured_llm.invoke(prompt)
    except Exception as e:
        print(f"Warning: Decomposition LLM call failed ({e}). Falling back to baseline Swin-Transformer change detection component graph.")
        from schemas import ParameterDetails
        component_graph = ComponentGraph(
            components=[
                Component(
                    name="Swin Transformer (RFN)",
                    type="encoder",
                    description="Visual backbone for Remote Sensing feature extraction.",
                    inputs=["Image"],
                    outputs=["Features"],
                    parameters={
                        "depth": ParameterDetails(value="Not specified", confidence="ASSUMED", rationale="Fallback baseline default"),
                        "patch_size": ParameterDetails(value="Not specified", confidence="ASSUMED", rationale="Fallback baseline default")
                    }
                ),
                Component(
                    name="RemoteCLIP Image Encoder",
                    type="encoder",
                    description="Frozen CLIP-based text/image semantic alignment encoder.",
                    inputs=["Image", "Text"],
                    outputs=["Embeddings"],
                    parameters={
                        "width": ParameterDetails(value="512", confidence="ASSUMED", rationale="Standard CLIP default")
                    }
                )
            ]
        )
    return component_graph

# Define LangGraph Node
def decomposition_node(state: AgentState) -> dict:
    parsed_sections = state["parsed_sections"]
    component_graph = run_decomposition_agent(parsed_sections)
    return {"component_graph": component_graph}

# Compile LangGraph Workflow
workflow = StateGraph(AgentState)
workflow.add_node("decomposition", decomposition_node)
workflow.add_edge(START, "decomposition")
workflow.add_edge("decomposition", END)
graph = workflow.compile()
