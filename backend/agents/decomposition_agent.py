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

def run_decomposition_agent(
    parsed_sections: dict, 
    model_name: str = "qwen2.5-coder:1.5b",
    paper_doc: Any = None
) -> ComponentGraph:
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
                
    # Retrieve Grounded RAG architectural evidence if paper_doc is provided
    rag_context = ""
    if paper_doc:
        from retrieval import generate_local_embedding, generate_grounded_evidence
        
        print("[Decomposition Agent] Querying local pgvector database for grounded architectural evidence...")
        rag_query = (
            "What visual backbones, encoders, decoders, fusion modules, loss functions, "
            "learning rate, batch size, epochs, and optimizer are used in this paper?"
        )
        try:
            query_vector = generate_local_embedding(rag_query)
            evidence_packages = generate_grounded_evidence(rag_query, query_vector, top_k=5)
            
            evidence_blocks = []
            for ev in evidence_packages:
                evidence_blocks.append(
                    f"--- Source: '{ev['section']}' (Page {ev['page']}) ---\n{ev['content']}"
                )
            rag_context = "\n\n".join(evidence_blocks)
            print(f"[Decomposition Agent] Grounded context loaded ({len(evidence_packages)} evidence packages).")
        except Exception as e:
            print(f"Warning: RAG evidence query failed: {e}")

    # num_predict=1024 prevents the LLM looping through parameter fields endlessly
    print(f"Initializing ChatOllama with model '{model_name}'...")
    llm = ChatOllama(model=model_name, temperature=0.0, num_ctx=4096, num_predict=1024)
    structured_llm = llm.with_structured_output(ComponentGraph)

    prompt = (
        "You are an expert ML architect. Decompose the research paper METHOD section into named architecture components.\n\n"
    )
    
    if rag_context:
        prompt += f"--- GROUNDED RAG EVIDENCE ---\n{rag_context[:2000]}\n\n"
        
    prompt += (
        f"--- METHOD SECTION (first 3000 chars) ---\n{method_content[:3000]}\n\n"
        f"--- EXPERIMENTS SECTION (first 1000 chars) ---\n{experiments_content[:1000] if experiments_content else 'N/A'}\n\n"
        "STRICT RULES:\n"
        "- Extract 2-5 SPECIFIC named components (e.g. 'Swin Transformer', 'SFN', 'Cross-Entropy Loss').\n"
        "- type must be one of: 'encoder', 'fusion', 'decoder', 'loss', 'training'.\n"
        "- Each parameter needs: value (concrete or 'Not specified'), confidence ('CONFIRMED'/'ASSUMED'), rationale (1 sentence).\n"
        "- Extract max 5 parameters per component (the most important ones only).\n"
        "- Do NOT repeat yourself. Each field must be unique."
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
            ],
            edges=[]
        )
        
    # Programmatic Dependency Adjacency Resolver (Day 20 Component Graph)
    if not component_graph.edges:
        derived_edges = []
        components = component_graph.components
        
        # 1. Resolve edges by input/output tensor overlaps
        for comp_a in components:
            for comp_b in components:
                if comp_a.name == comp_b.name:
                    continue
                # Map outputs of comp_a to inputs of comp_b
                for out_tensor in comp_a.outputs:
                    out_clean = out_tensor.lower().strip()
                    if not out_clean or out_clean in ["loss value", "training steps", "gradients", "model parameters"]:
                        continue
                    for in_tensor in comp_b.inputs:
                        in_clean = in_tensor.lower().strip()
                        if out_clean == in_clean or out_clean in in_clean or in_clean in out_clean:
                            edge = {"source": comp_a.name, "target": comp_b.name}
                            if edge not in derived_edges:
                                derived_edges.append(edge)
                                
        # 2. Fallback / supplementary sequence alignment (Type-based flow structure)
        # Standard: encoder -> fusion -> decoder -> loss -> training
        encoders = [c.name for c in components if c.type == "encoder"]
        fusions = [c.name for c in components if c.type == "fusion"]
        decoders = [c.name for c in components if c.type == "decoder"]
        losses = [c.name for c in components if c.type == "loss"]
        trainings = [c.name for c in components if c.type == "training"]
        
        # If no programmatic tensor edges could be found, build the type-based sequence flow graph
        if not derived_edges:
            next_targets = fusions if fusions else (decoders if decoders else losses)
            for enc in encoders:
                for target in next_targets:
                    derived_edges.append({"source": enc, "target": target})
            
            for fus in fusions:
                for dec in decoders:
                    derived_edges.append({"source": fus, "target": dec})
                    
            for dec in decoders:
                for loss in losses:
                    derived_edges.append({"source": dec, "target": loss})
                    
            for loss in losses:
                for tr in trainings:
                    derived_edges.append({"source": loss, "target": tr})
                    
        component_graph.edges = derived_edges
        
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
