import os
import json
import sys
from typing import List, Dict, TypedDict
from pydantic import BaseModel, Field
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END

# Define Pydantic models for structured architecture graph
class Component(BaseModel):
    name: str = Field(description="The name of the component, e.g., 'Swin Transformer Encoder', 'Side Fusion Network', 'Bridging Module'")
    type: str = Field(description="The category of the component. Must be one of: 'encoder', 'fusion', 'decoder', 'loss', 'training'")
    description: str = Field(description="A brief description of what this component does in the paper's architecture")
    inputs: List[str] = Field(description="List of input data streams, feature maps, or tensors it accepts")
    outputs: List[str] = Field(description="List of outputs or tensors it produces")
    hyperparameters: Dict[str, str] = Field(
        description="Key-value pairs of hyperparameters mentioned in the text (e.g. channels, batch size, learning rates, epochs, optimizer, etc.)"
    )

class ComponentGraph(BaseModel):
    components: List[Component] = Field(description="List of all structural architecture components extracted from the method section")

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

    if not method_content:
        raise ValueError("Error: Method section (e.g., 'III. METHOD') was not found in the parsed paper sections.")

    # Initialize Ollama model with structured output
    print(f"Initializing ChatOllama with model '{model_name}'...")
    llm = ChatOllama(model=model_name, temperature=0.0)
    structured_llm = llm.with_structured_output(ComponentGraph)

    # Prompt instructing the LLM
    prompt = (
        "You are an expert machine learning architect. Your task is to analyze the METHOD and EXPERIMENTS sections of a research paper "
        "and decompose its architecture into a structured component graph.\n\n"
        f"--- METHOD SECTION CONTENT ---\n{method_content}\n\n"
        f"--- EXPERIMENTS SECTION CONTENT ---\n{experiments_content}\n\n"
        "Instructions:\n"
        "Identify and extract all core components. Categorize each component type as one of:\n"
        "- 'encoder' (e.g., visual encoders, backbones)\n"
        "- 'fusion' (e.g., cross-attention modules, feature fusions, bridges)\n"
        "- 'decoder' (e.g., mask heads, segmentation decoders)\n"
        "- 'loss' (e.g., cross-entropy losses, custom distance metrics)\n"
        "- 'training' (e.g., optimizer, learning rate schedule, batch size, training epochs)\n\n"
        "For each component, extract its name, description, inputs, outputs, and any mentioned hyperparameters.\n\n"
        "CRITICAL WARNING:\n"
        "- Extract only CONCRETE values and numbers mentioned in the text (e.g., batch_size: '24', learning_rate: '0.001', epochs: '250', width: '512').\n"
        "- Do NOT use template variables or placeholders like '{batch_size}', '{learning_rate}', or '{width}'.\n"
        "- If a hyperparameter value is not mentioned in the text, use 'Not specified' or omit it, but NEVER generate curly-brace placeholders."
    )

    print("Sending request to local Ollama for structured method decomposition...")
    component_graph = structured_llm.invoke(prompt)
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
