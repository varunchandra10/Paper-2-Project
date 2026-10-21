from datetime import datetime, timezone
from typing import Dict, Any
from app.graph.state import PipelineState
from app.core.tracer import AgentTracer


def specification_node(state: PipelineState) -> dict:
    """Synthesizes structured architecture specifications from build sequence and parameters."""
    build_seq = state.get("build_sequence")
    params = state.get("extracted_parameters")
    comp_graph = state.get("component_graph", {})
    paper_id = state.get("paper_id") or (state["paper_doc"].paper_id if state.get("paper_doc") else "paper")
    model = state.get("model_name", "qwen2.5-coder:1.5b")

    modules_spec = []
    if build_seq and hasattr(build_seq, "steps"):
        for step in build_seq.steps:
            modules_spec.append({
                "step_number": getattr(step, "step_number", len(modules_spec) + 1),
                "module_name": getattr(step, "module_name", "model"),
                "description": getattr(step, "description", ""),
                "dependencies": getattr(step, "dependencies", []),
                "estimated_loc": getattr(step, "estimated_loc", 50),
            })
    else:
        modules_spec.append({
            "step_number": 1,
            "module_name": "model",
            "description": "Primary deep learning architecture module",
            "dependencies": [],
            "estimated_loc": 60,
        })

    spec = {
        "paper_id": paper_id,
        "target_framework": "PyTorch",
        "modules": modules_spec,
        "parameters": params.model_dump() if params and hasattr(params, "model_dump") else {},
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    tracer = AgentTracer()
    tracer.log_step(
        paper_id,
        "ARCHITECTURE_SPECIFICATION",
        "success",
        f"Synthesized modular specification for {len(modules_spec)} architecture components.",
        duration_ms=500,
        model_used=model
    )

    history = list(state.get("history_trace", []))
    history.append({
        "node": "specification_node",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "modules_count": len(modules_spec)
    })

    return {
        "specification": spec,
        "history_trace": history
    }
