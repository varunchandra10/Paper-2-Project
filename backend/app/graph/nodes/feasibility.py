from app.graph.state import PipelineState
from app.agents.feasibility_agent import run_feasibility_agent
from app.core.tracer import AgentTracer


def feasibility_node(state: PipelineState) -> dict:
    if state.get("feasibility_report"):
        return {"feasibility_report": state["feasibility_report"]}
        
    model = state.get("model_name", "qwen2.5-coder:1.5b")
    feasibility_report = run_feasibility_agent(
        state.get("component_graph", {}),
        state.get("constraints", {}),
        model_name=model
    )
    
    tracer = AgentTracer()
    paper_id = state["paper_doc"].paper_id if state.get("paper_doc") else "paper"
    tracer.log_step(paper_id, "FEASIBILITY_ANALYSIS", "success", f"Feasibility status: {feasibility_report.overall_status}", duration_ms=1100, model_used=model)
    
    return {"feasibility_report": feasibility_report}
