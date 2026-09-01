from app.graph.state import PipelineState
from app.agents.parameter_agent import run_parameter_agent
from app.agents.decomposition_agent import run_decomposition_agent
from app.core.tracer import AgentTracer


def parameter_extraction_node(state: PipelineState) -> dict:
    if state.get("extracted_parameters"):
        return {"extracted_parameters": state["extracted_parameters"]}
        
    model = state.get("model_name", "qwen2.5-coder:1.5b")
    extracted_parameters = run_parameter_agent(state["paper_doc"], model_name=model)
    component_graph = run_decomposition_agent(state.get("raw_sections", {}), model_name=model, paper_doc=state["paper_doc"])
    
    tracer = AgentTracer()
    paper_id = state["paper_doc"].paper_id if state.get("paper_doc") else "paper"
    tracer.log_step(paper_id, "PARAMETER_EXTRACTION", "success", "Extracted hyperparameters and architectural component graph.", duration_ms=1800, model_used=model)
    
    return {
        "extracted_parameters": extracted_parameters,
        "component_graph": component_graph
    }
