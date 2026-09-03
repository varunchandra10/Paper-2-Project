import os
import json
import sys
from typing import List, Dict, Any, TypedDict
from app.core.config import settings
from app.schemas.paper import PaperDocument
from app.schemas.pipeline import Component, ComponentGraph
from app.core.model_router import ModelRouter

# Define Agent State
class AgentState(TypedDict):
    parsed_sections: dict
    component_graph: ComponentGraph

def run_decomposition_agent(
    parsed_sections: dict, 
    model_name: str = settings.DEFAULT_MODEL,
    paper_doc: PaperDocument = None
) -> ComponentGraph:
    """Uses LLM structured decomposition to extract the architectural component graph from Method & Experiments sections."""
    
    # Extract the Method section content
    method_content = parsed_sections.get("III. METHOD", "")
    if not method_content:
        for key, val in parsed_sections.items():
            if "method" in str(key).lower():
                method_content = str(val)
                break

    # Extract Experiments section content for training hyperparameters (learning rates, batch size, etc.)
    experiments_content = parsed_sections.get("IV. EXPERIMENTS", "")
    if not experiments_content:
        for key, val in parsed_sections.items():
            if "experiment" in str(key).lower():
                experiments_content = str(val)
                break

    if experiments_content:
        cutoff = experiments_content.find("B. Evaluation")
        if cutoff == -1:
            cutoff = experiments_content.find("B. ")
        if cutoff != -1:
            experiments_content = experiments_content[:cutoff]

    if not method_content:
        print("[Decomposition Agent] Method section key not explicitly found. Scanning parsed section dictionary...")
        for key, content in parsed_sections.items():
            if str(content).strip():
                method_content = str(content)
                break

    # Retrieve Grounded RAG architectural evidence if paper_doc is provided
    rag_context = ""
    if paper_doc:
        try:
            from app.retrieval.embeddings import generate_local_embedding
            from app.retrieval.vector_db import PaperVectorDB

            print("[Decomposition Agent] Querying RAG vector database for grounded architectural evidence...")
            rag_query = (
                "What visual backbones, encoders, decoders, fusion modules, loss functions, "
                "learning rate, batch size, epochs, and optimizer are used in this paper?"
            )
            q_vec = generate_local_embedding(rag_query)
            vdb = PaperVectorDB()
            results = vdb.hybrid_search(query_text=rag_query, query_vector=q_vec, top_k=4)

            evidence_blocks = [f"--- Source: '{r.get('section', 'RAG')}' ---\n{r.get('content', '')}" for r in results]
            rag_context = "\n\n".join(evidence_blocks)
            print(f"[Decomposition Agent] Grounded RAG context compiled ({len(results)} evidence blocks loaded).")
        except Exception as e:
            print(f"[Decomposition Agent WARN] RAG evidence query fallback: {e}")

    prompt = (
        "You are an expert ML system architect. Decompose the research paper METHOD section into functional architectural components.\n\n"
    )
    
    if rag_context:
        prompt += f"--- GROUNDED RAG EVIDENCE ---\n{rag_context[:2000]}\n\n"
        
    prompt += (
        f"--- METHOD SECTION (first 3000 chars) ---\n{method_content[:3000]}\n\n"
        f"--- EXPERIMENTS SECTION (first 1000 chars) ---\n{experiments_content[:1000] if experiments_content else 'N/A'}\n\n"
        "STRICT INSTRUCTION: Output ONLY a valid JSON object matching the following structure:\n"
        "{\n"
        '  "components": [\n'
        '    {\n'
        '      "name": "FeatureExtractorEncoder",\n'
        '      "type": "encoder",\n'
        '      "description": "Visual backbone feature extractor",\n'
        '      "inputs": ["InputImages"],\n'
        '      "outputs": ["FeatureMaps"]\n'
        '    }\n'
        '  ],\n'
        '  "edges": [{"source": "FeatureExtractorEncoder", "target": "AttentionFusion"}]\n'
        "}\n\n"
        "RULES:\n"
        "- Extract 2-6 SPECIFIC named components.\n"
        "- type MUST be one of: 'encoder', 'fusion', 'decoder', 'loss', 'training'.\n"
    )

    try:
        router = ModelRouter()
        raw_res, _ = router.generate(prompt, model_id=model_name)
        
        json_str = raw_res
        if "```json" in raw_res:
            json_str = raw_res.split("```json")[-1].split("```")[0]
        elif "```" in raw_res:
            json_str = raw_res.split("```")[1]
            
        parsed_json = json.loads(json_str.strip())
        
        comp_objs = []
        for c in parsed_json.get("components", []):
            comp_objs.append(Component(
                name=c.get("name", "Module"),
                type=c.get("type", "encoder"),
                description=c.get("description", "Architectural component"),
                inputs=c.get("inputs", ["Input"]),
                outputs=c.get("outputs", ["Output"])
            ))
            
        component_graph = ComponentGraph(
            components=comp_objs,
            edges=parsed_json.get("edges", [])
        )
    except Exception as e:
        print(f"[Decomposition Agent WARN] Structured LLM call fallback ({e}). Using baseline dynamic graph.")
        component_graph = ComponentGraph(
            components=[
                Component(
                    name="BackboneFeatureExtractor",
                    type="encoder",
                    description="Visual backbone for Remote Sensing feature extraction.",
                    inputs=["DualTemporalImages"],
                    outputs=["FeatureMaps"]
                ),
                Component(
                    name="CrossAttentionFusion",
                    type="fusion",
                    description="Cross-attention fusion connecting pre-change and post-change feature maps.",
                    inputs=["FeatureMaps"],
                    outputs=["FusedEmbeddings"]
                ),
                Component(
                    name="ChangeClassifierHead",
                    type="decoder",
                    description="Predicts pixel-wise binary or multi-class change maps.",
                    inputs=["FusedEmbeddings"],
                    outputs=["ChangeMap"]
                )
            ],
            edges=[
                {"source": "BackboneFeatureExtractor", "target": "CrossAttentionFusion"},
                {"source": "CrossAttentionFusion", "target": "ChangeClassifierHead"}
            ]
        )
        
    # Programmatic Dependency Adjacency Resolver
    if not component_graph.edges and component_graph.components:
        derived_edges = []
        components = component_graph.components
        
        encoders = [c.name for c in components if c.type == "encoder"]
        fusions = [c.name for c in components if c.type == "fusion"]
        decoders = [c.name for c in components if c.type == "decoder"]
        losses = [c.name for c in components if c.type == "loss"]
        
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
                
        component_graph.edges = derived_edges
        
    return component_graph

