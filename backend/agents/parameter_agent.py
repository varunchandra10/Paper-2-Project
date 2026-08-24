import os
import json
import sys
from typing import List, Dict, TypedDict, Any
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END
from schemas import ProjectParameter, ExtractedParameters, PaperDocument

# Define LangGraph State
class ParameterAgentState(TypedDict):
    paper_doc: PaperDocument
    extracted_parameters: ExtractedParameters

# Day 12 status to confidence level mapping
CONFIDENCE_MAP = {
    "EXPLICIT": 1.0,
    "DERIVED": 0.9,
    "INFERRED": 0.8,
    "ASSUMED": 0.5,
    "UNKNOWN": 0.0
}

def run_parameter_agent(paper_doc: PaperDocument, model_name: str = "qwen2.5-coder:1.5b") -> ExtractedParameters:
    """Queries local pgvector for parameter evidence and extracts 11 experimental/architectural parameters."""
    
    from retrieval import generate_local_embedding, generate_grounded_evidence
    
    print("[Parameter Agent] Querying pgvector for experimental hyperparameters and hardware metadata...")
    
    # Run structured RAG queries to cover all 11 target parameters
    rag_queries = [
        "What model architecture backbone, visual encoder, text encoder, or CLIP model is used?",
        "What datasets (e.g. LEVIR-CD, WHU-CD, CDD) are used for training and evaluation?",
        "What optimizer, learning rate, training batch size, and epochs were used during experiments?",
        "What loss function, learning rate scheduler, input size, spatial resolution, and data augmentations are used?",
        "What compute hardware (GPUs, CPU, VRAM) is used for training and testing?"
    ]
    
    evidence_blocks = []
    for q in rag_queries:
        try:
            query_vector = generate_local_embedding(q)
            results = generate_grounded_evidence(q, query_vector, top_k=2)
            for res in results:
                block = f"--- RAG Context ({res['section']}, Page {res['page']}) ---\n{res['content']}"
                if block not in evidence_blocks:
                    evidence_blocks.append(block)
        except Exception as e:
            print(f"Warning: RAG query for parameter extraction failed: {e}")
            
    rag_context = "\n\n".join(evidence_blocks)
    print(f"[Parameter Agent] Grounded context compiled ({len(evidence_blocks)} evidence units loaded).")

    # num_predict=768 prevents looping in parameter value/rationale fields
    print(f"Initializing ChatOllama with model '{model_name}'...")
    llm = ChatOllama(model=model_name, temperature=0.0, num_ctx=4096, num_predict=768)
    structured_llm = llm.with_structured_output(ExtractedParameters)

    prompt = (
        "You are an academic paper analysis agent. Your task is to extract 11 specific training and architectural parameters "
        "from the provided research paper context.\n\n"
        "--- GROUNDED PAPER CONTEXT ---\n"
        f"{rag_context}\n\n"
        "Extract the following 11 parameters:\n"
        "1. model (e.g. VLCD, Swin-T, ResNet-18, Siamese backbone)\n"
        "2. dataset (e.g. LEVIR-CD, WHU-CD, CDD)\n"
        "3. optimizer (e.g. AdamW, Adam, SGD)\n"
        "4. learning_rate (e.g. 2e-4, 0.001)\n"
        "5. batch_size (e.g. 16, 8, 4)\n"
        "6. epochs (e.g. 50, 100, 200)\n"
        "7. loss (e.g. Binary Cross Entropy, Contrastive Loss, custom losses)\n"
        "8. scheduler (e.g. Cosine Annealing, StepLR)\n"
        "9. input_size (e.g. 256x256, 512x512)\n"
        "10. augmentation (e.g. random flip, rotate, crop, scale)\n"
        "11. hardware (e.g. NVIDIA RTX 4090, A100 GPU, or CPU)\n\n"
        "Instructions:\n"
        "- For every parameter, extract:\n"
        "  - 'value': The concrete parameter value (e.g. 'AdamW', '0.0002', 'LEVIR-CD', or 'Not specified' if missing).\n"
        "  - 'source': The location/coordinates in the paper (e.g. 'Section IV-B, Page 8' or 'Not found').\n"
        "  - 'status': Enforce one of these tags:\n"
        "    * 'EXPLICIT': The parameter is explicitly stated in the context.\n"
        "    * 'INFERRED': You deduced it using standard model configurations.\n"
        "    * 'ASSUMED': Missing from text, and you assumed a default practice.\n"
        "    * 'DERIVED': Calculated or combined from multiple parts.\n"
        "    * 'UNKNOWN': Completely missing and unresolvable.\n"
        "  - 'confidence': Pass 0.0 for now (it will be programmatically verified and overridden based on the status).\n\n"
        "CRITICAL: Avoid placeholders like '{batch_size}' or '{learning_rate}'. Output only concrete values."
    )

    try:
        print("Sending request to local Ollama for structured parameter extraction...")
        extracted = structured_llm.invoke(prompt)
    except Exception as e:
        print(f"Warning: Parameter extraction LLM call failed ({e}). Using empty parameter fallbacks.")
        empty_param = ProjectParameter(value="Not specified", source="Not found", status="UNKNOWN", confidence=0.0)
        extracted = ExtractedParameters(
            model=empty_param, dataset=empty_param, optimizer=empty_param, learning_rate=empty_param,
            batch_size=empty_param, epochs=empty_param, loss=empty_param, scheduler=empty_param,
            input_size=empty_param, augmentation=empty_param, hardware=empty_param
        )

    # Programmatic Confidence/Status Alignment Guardrail (Day 12 Rules)
    for field_name in extracted.__class__.model_fields.keys():
        param_obj = getattr(extracted, field_name)
        status_clean = str(param_obj.status).upper().strip()
        if status_clean not in CONFIDENCE_MAP:
            status_clean = "UNKNOWN"
        
        # Override values to enforce correct status and confidence mapping
        param_obj.status = status_clean
        param_obj.confidence = CONFIDENCE_MAP[status_clean]
        
    return extracted

# Define LangGraph Node
def parameter_extraction_node(state: ParameterAgentState) -> dict:
    paper_doc = state["paper_doc"]
    extracted_parameters = run_parameter_agent(paper_doc)
    return {"extracted_parameters": extracted_parameters}

# Compile Workflow
workflow = StateGraph(ParameterAgentState)
workflow.add_node("parameter_extraction", parameter_extraction_node)
workflow.add_edge(START, "parameter_extraction")
workflow.add_edge("parameter_extraction", END)
graph = workflow.compile()
