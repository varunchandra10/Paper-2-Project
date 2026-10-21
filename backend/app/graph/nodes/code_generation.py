from datetime import datetime, timezone
from app.graph.state import PipelineState
from app.agents.code_gen_agent import run_code_gen_agent
from app.core.tracer import AgentTracer


def code_generation_node(state: PipelineState) -> dict:
    """Synthesizes candidate PyTorch implementation code using the dual-engine synthesizer."""
    model = state.get("model_name", "qwen2.5-coder:1.5b")
    params = state.get("extracted_parameters")
    paper_id = state.get("paper_id") or (state["paper_doc"].paper_id if state.get("paper_doc") else "paper")
    comp_graph = state.get("component_graph")

    # If code is already supplied (e.g. pre-set in tests), reuse it
    sample_code = state.get("sample_code")
    if not sample_code:
        sample_code = run_code_gen_agent(
            module_name="model",
            parameters=params,
            model_name=model,
            paper_id=paper_id,
            component_graph=comp_graph
        )

    tracer = AgentTracer()
    tracer.log_step(
        paper_id,
        "CODE_GENERATION",
        "success",
        f"Generated model implementation code ({len(sample_code.splitlines())} lines).",
        duration_ms=1200,
        model_used=model
    )

    history = list(state.get("history_trace", []))
    history.append({
        "node": "code_generation_node",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "code_lines": len(sample_code.splitlines())
    })

    return {
        "sample_code": sample_code,
        "history_trace": history
    }
