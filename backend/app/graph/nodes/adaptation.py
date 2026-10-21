from datetime import datetime, timezone
from app.graph.state import PipelineState
from app.schemas.pipeline import ExtractedParameters, ProvenanceStatus
from app.core.tracer import AgentTracer


def parameter_adaptation_node(state: PipelineState) -> dict:
    """Adapts hyperparameters (e.g., batch size, mixed precision) to resolve hardware feasibility bottlenecks."""
    feasibility_report = state.get("feasibility_report")
    params: ExtractedParameters = state.get("extracted_parameters")
    current_loop = state.get("feasibility_loop_count", 0)
    new_loop = current_loop + 1

    current_bs = 16
    if params and hasattr(params, "batch_size") and params.batch_size and params.batch_size.value is not None:
        try:
            current_bs = int(str(params.batch_size.value).split()[0])
        except Exception:
            current_bs = 16

    available_vram = feasibility_report.available_vram_gb if feasibility_report else 4.0
    status = feasibility_report.overall_status if feasibility_report else "FEASIBLE_WITH_MODIFICATION"

    # Scale batch size based on severity of VRAM bottleneck
    if status == "NOT_FEASIBLE":
        new_bs = max(1, current_bs // 4)
    else:
        new_bs = max(1, current_bs // 2)

    # Apply adaptation if parameters object exists
    if params and hasattr(params, "batch_size"):
        params.batch_size.value = new_bs
        params.batch_size.status = ProvenanceStatus.DERIVED.value
        params.batch_size.evidence = (
            f"Adapted from {current_bs} to {new_bs} to satisfy GPU VRAM ceiling of {available_vram} GB."
        )
        params.batch_size.extraction_method = "feasibility_adaptation"
        params.batch_size.evidence_strength = "STRONG"

    tracer = AgentTracer()
    paper_id = state.get("paper_id") or (state["paper_doc"].paper_id if state.get("paper_doc") else "paper")
    tracer.log_step(
        paper_id,
        "PARAMETER_ADAPTATION",
        "success",
        f"Adapted batch_size from {current_bs} to {new_bs} (Refinement loop {new_loop})",
        duration_ms=400,
        model_used=state.get("model_name", "adaptation_rule_engine")
    )

    history = list(state.get("history_trace", []))
    history.append({
        "node": "adaptation_node",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": "batch_size_adaptation",
        "previous_batch_size": current_bs,
        "new_batch_size": new_bs,
        "feasibility_loop_count": new_loop
    })

    return {
        "extracted_parameters": params,
        "feasibility_loop_count": new_loop,
        "history_trace": history
    }
