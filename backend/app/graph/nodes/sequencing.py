from datetime import datetime, timezone
from app.graph.state import PipelineState
from app.agents.sequencing_agent import run_sequencing_agent
from app.agents.report_agent import run_report_agent
from app.core.dag_validator import DAGValidator
from app.core.tracer import AgentTracer


def sequencing_node(state: PipelineState) -> dict:
    """Constructs, validates, and topographically sorts the modular DAG build sequence."""
    model = state.get("model_name", "qwen2.5-coder:1.5b")
    build_sequence = run_sequencing_agent(
        state.get("component_graph", {}),
        state.get("feasibility_report"),
        model_name=model
    )

    # Validate DAG invariants
    dag_val = DAGValidator.validate(build_sequence.steps)
    if not dag_val.is_valid:
        print(f"[Sequencing Node WARN] Unexpected DAG validation failure in node: {[i.code for i in dag_val.issues]}")

    report = run_report_agent({}, state.get("feasibility_report"), build_sequence, model_name=model)
    
    paper_id = state.get("paper_id") or (state["paper_doc"].paper_id if state.get("paper_doc") else "paper")
    tracer = AgentTracer()
    tracer.log_step(
        paper_id,
        "BUILD_SEQUENCING",
        "success" if dag_val.is_valid else "warning",
        f"Generated modular adaptation build sequence ({build_sequence.total_steps} milestones, DAG valid={dag_val.is_valid}).",
        duration_ms=900,
        model_used=model
    )

    history = list(state.get("history_trace", []))
    history.append({
        "node": "sequencing_node",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_steps": build_sequence.total_steps,
        "is_valid_dag": dag_val.is_valid,
        "execution_order": dag_val.execution_order
    })
    
    return {
        "build_sequence": build_sequence,
        "report": report,
        "history_trace": history
    }
