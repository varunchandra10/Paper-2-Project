from datetime import datetime, timezone
from app.graph.state import PipelineState
from app.core.code_verifier import code_verifier
from app.core.tracer import AgentTracer


def evaluation_node(state: PipelineState) -> dict:
    """Performs 3-layer verification (AST syntax, hyperparameter grounding, sandboxed forward pass)."""
    sample_code = state.get("sample_code", "")
    params = state.get("extracted_parameters")
    paper_id = state.get("paper_id") or (state["paper_doc"].paper_id if state.get("paper_doc") else "paper")
    model = state.get("model_name", "qwen2.5-coder:1.5b")
    repair_count = state.get("code_repair_loop_count", 0)

    param_dict = None
    if params and hasattr(params, "model_dump"):
        param_dict = params.model_dump()

    # Perform full 3-layer evaluation
    raw_res = code_verifier.evaluate_candidate(
        code=sample_code,
        file_path="model.py",
        parameters=param_dict
    )

    l1 = raw_res.get("layer1_ast", {})
    l2 = raw_res.get("layer2_grounding", {})
    l3 = raw_res.get("layer3_exec", {})

    layer1 = bool(l1.get("valid", False))
    layer2 = float(l2.get("score", 0.0))
    layer3 = bool(l3.get("passed", False)) if l3.get("executed") else layer1
    is_passed = bool(raw_res.get("is_valid", False)) and (not l3.get("executed") or layer3)
    status = "PASSED" if is_passed else "FAILED"
    error_msg = l3.get("error") or l1.get("msg") if not is_passed else None

    verif_res = {
        "status": status,
        "layer1_syntax": layer1,
        "layer2_grounding": layer2,
        "layer3_execution": layer3,
        "error": error_msg,
        "output_shape": l3.get("output_shape"),
        "total_score": raw_res.get("total_score", 0.0),
        "repair_loop_count": repair_count
    }

    tracer = AgentTracer()
    tracer.log_step(
        paper_id,
        "CODE_EVALUATION",
        "success" if is_passed else "warning",
        f"Evaluation status: {status} (L1_Syntax={layer1}, L2_Grounding={layer2}%, L3_Exec={layer3}, Error={error_msg})",
        duration_ms=800,
        model_used=model
    )

    history = list(state.get("history_trace", []))
    history.append({
        "node": "evaluation_node",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "layer1_syntax": layer1,
        "layer3_execution": layer3,
        "error": error_msg,
        "repair_loop_count": repair_count
    })

    return {
        "verification_result": verif_res,
        "parameters_approved": is_passed,
        "history_trace": history
    }
