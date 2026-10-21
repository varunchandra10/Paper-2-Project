from datetime import datetime, timezone
from app.graph.state import PipelineState
from app.agents.feasibility_agent import run_feasibility_agent
from app.core.tracer import AgentTracer


def feasibility_node(state: PipelineState) -> dict:
    """Evaluates mathematical VRAM feasibility against hardware constraints.
    Re-evaluates if parameters were adapted during a refinement loop.
    """
    loop_count = state.get("feasibility_loop_count", 0)
    
    # If already computed and no refinement loop was executed, reuse cached report
    if state.get("feasibility_report") and loop_count == 0 and not state.get("_force_recompute_feasibility"):
        return {"feasibility_report": state["feasibility_report"]}

    model = state.get("model_name", "qwen2.5-coder:1.5b")
    params = state.get("extracted_parameters")
    
    feasibility_report = run_feasibility_agent(
        component_graph=state.get("component_graph", {}),
        constraints=state.get("constraints", {}),
        parameters=params,
        model_name=model
    )

    tracer = AgentTracer()
    paper_id = state.get("paper_id") or (state["paper_doc"].paper_id if state.get("paper_doc") else "paper")
    tracer.log_step(
        paper_id,
        "FEASIBILITY_ANALYSIS",
        "success",
        f"Feasibility status: {feasibility_report.overall_status} (VRAM {feasibility_report.estimated_vram_gb} GB vs {feasibility_report.available_vram_gb} GB, loop={loop_count})",
        duration_ms=1100,
        model_used=model
    )

    # Append to history trace
    history = list(state.get("history_trace", []))
    history.append({
        "node": "feasibility_node",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": feasibility_report.overall_status,
        "estimated_vram_gb": feasibility_report.estimated_vram_gb,
        "available_vram_gb": feasibility_report.available_vram_gb,
        "feasibility_loop_count": loop_count
    })

    return {
        "feasibility_report": feasibility_report,
        "history_trace": history
    }
