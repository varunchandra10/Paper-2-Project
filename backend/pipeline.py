from schemas import PipelineOutput, PaperMetadata, ComponentGraph
from ingestion_agent import run_ingestion_agent
from decomposition_agent import run_decomposition_agent
from gap_agent import run_gap_agent

def run_pipeline(parsed_sections: dict, model_name: str = "qwen2.5-coder:1.5b") -> PipelineOutput:
    """Chains Ingestion, Decomposition, and Gap-Finding end-to-end."""
    
    print("\n[Pipeline] Step 1: Running Ingestion Agent...")
    metadata = run_ingestion_agent(parsed_sections, model_name)
    
    print("\n[Pipeline] Step 2: Running Method Decomposition Agent...")
    component_graph = run_decomposition_agent(parsed_sections, model_name)
    
    print("\n[Pipeline] Step 3: Running Gap-Finding Agent...")
    gap_filled_graph = run_gap_agent(component_graph, model_name)
    
    print("\n[Pipeline] Integration successful! Building final consolidated output.")
    return PipelineOutput(metadata=metadata, component_graph=gap_filled_graph)
