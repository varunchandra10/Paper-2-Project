from app.graph.state import PipelineState
from app.agents.sequencing_agent import run_sequencing_agent
from app.agents.report_agent import run_report_agent
from app.core.tracer import AgentTracer


def sequencing_node(state: PipelineState) -> dict:
    model = state.get("model_name", "qwen2.5-coder:1.5b")
    build_sequence = run_sequencing_agent(
        state.get("component_graph", {}),
        state.get("feasibility_report"),
        model_name=model
    )
    report = run_report_agent({}, state.get("feasibility_report"), build_sequence, model_name=model)
    
    tracer = AgentTracer()
    paper_id = state["paper_doc"].paper_id if state.get("paper_doc") else "paper"
    tracer.log_step(paper_id, "BUILD_SEQUENCING", "success", "Generated modular adaptation build sequence.", duration_ms=900, model_used=model)
    
    return {
        "build_sequence": build_sequence,
        "report": report
    }
