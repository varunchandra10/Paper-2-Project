import time
from langgraph.graph import StateGraph, START, END
from app.graph.state import PipelineState
from app.graph.nodes.ingestion import ingestion_node
from app.graph.nodes.extraction import parameter_extraction_node
from app.graph.nodes.feasibility import feasibility_node
from app.graph.nodes.adaptation import parameter_adaptation_node
from app.graph.nodes.sequencing import sequencing_node
from app.graph.nodes.specification import specification_node
from app.graph.nodes.code_generation import code_generation_node
from app.graph.nodes.evaluation import evaluation_node
from app.graph.nodes.repair import code_repair_node
from app.core.events import (
    emit_node_start,
    emit_node_complete,
    emit_refinement,
    emit_retry,
    emit_node_error
)


def wrap_node_with_telemetry(node_name: str, node_func):
    """Wraps a LangGraph node to emit real, ordered execution events with true timing and status."""
    def wrapped_node(state: PipelineState) -> dict:
        job_id = state.get("job_id", "")
        paper_id = state.get("paper_id") or (state.get("paper_doc").paper_id if state.get("paper_doc") else "paper")

        emit_node_start(job_id, paper_id, node_name)
        start_time = time.time()

        try:
            result = node_func(state)
            duration_ms = int((time.time() - start_time) * 1000)

            # Node-specific structured domain event emissions
            if node_name == "adaptation_node":
                cur_loop = result.get("feasibility_loop_count", 1)
                emit_refinement(
                    job_id=job_id,
                    paper_id=paper_id,
                    node_name=node_name,
                    reason="Hardware constraint adaptation applied",
                    attempt=cur_loop
                )
            elif node_name == "code_repair_node":
                repair_loop = result.get("code_repair_loop_count", 1)
                verif_res = state.get("verification_result", {})
                emit_retry(
                    job_id=job_id,
                    paper_id=paper_id,
                    node_name=node_name,
                    attempt=repair_loop,
                    max_retries=state.get("max_repair_retries", 2),
                    error_summary=verif_res.get("error", "Code verification failure")[:120]
                )
            elif node_name == "evaluation_node":
                verif_res = result.get("verification_result", {})
                if verif_res.get("status") == "FAILED":
                    emit_node_error(
                        job_id=job_id,
                        paper_id=paper_id,
                        node_name=node_name,
                        error_message=verif_res.get("error", "Verification checks failed"),
                        metadata={"layer1_syntax": verif_res.get("layer1_syntax"), "layer3_execution": verif_res.get("layer3_execution")}
                    )

            emit_node_complete(
                job_id=job_id,
                paper_id=paper_id,
                node_name=node_name,
                metadata={"duration_ms": duration_ms}
            )
            return result
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            emit_node_error(
                job_id=job_id,
                paper_id=paper_id,
                node_name=node_name,
                error_message=str(e),
                metadata={"duration_ms": duration_ms}
            )
            raise e

    return wrapped_node


def route_feasibility(state: PipelineState) -> str:
    """Conditional router: evaluates whether parameters need adaptation to meet hardware constraints."""
    feasibility_report = state.get("feasibility_report")
    status = getattr(feasibility_report, "overall_status", "FEASIBLE") if feasibility_report else "FEASIBLE"
    loop_count = state.get("feasibility_loop_count", 0)
    max_retries = state.get("max_feasibility_retries", 2)

    # 1. Feasible: proceed to sequencing
    if status == "FEASIBLE":
        return "sequencing_node"

    # 2. Unfeasible but retries remain: loop through parameter adaptation
    if loop_count < max_retries:
        return "adaptation_node"

    # 3. Bounded exit: retries exhausted, proceed with best-effort adaptation notes
    return "sequencing_node"


def route_evaluation(state: PipelineState) -> str:
    """Conditional router: checks if generated code passed 3-layer verification or requires repair."""
    verif_res = state.get("verification_result", {})
    status = verif_res.get("status", "PASSED")
    repair_count = state.get("code_repair_loop_count", 0)
    max_retries = state.get("max_repair_retries", 2)

    # 1. Verification passed: terminate graph cleanly
    if status == "PASSED":
        return END

    # 2. Verification failed but repair budget remains: route to reflexion repair loop
    if repair_count < max_retries:
        return "code_repair_node"

    # 3. Bounded exit: repair budget exhausted, terminate with failure diagnostics
    return END


def build_pipeline_workflow() -> StateGraph:
    """Builds and compiles the bounded LangGraph V2 StateGraph with telemetry wrapping and self-correcting loops."""
    builder = StateGraph(PipelineState)

    # 1. Register all nodes with telemetry instrumentation
    builder.add_node("ingestion_node", wrap_node_with_telemetry("ingestion_node", ingestion_node))
    builder.add_node("extraction_node", wrap_node_with_telemetry("extraction_node", parameter_extraction_node))
    builder.add_node("feasibility_node", wrap_node_with_telemetry("feasibility_node", feasibility_node))
    builder.add_node("adaptation_node", wrap_node_with_telemetry("adaptation_node", parameter_adaptation_node))
    builder.add_node("sequencing_node", wrap_node_with_telemetry("sequencing_node", sequencing_node))
    builder.add_node("specification_node", wrap_node_with_telemetry("specification_node", specification_node))
    builder.add_node("code_generation_node", wrap_node_with_telemetry("code_generation_node", code_generation_node))
    builder.add_node("evaluation_node", wrap_node_with_telemetry("evaluation_node", evaluation_node))
    builder.add_node("code_repair_node", wrap_node_with_telemetry("code_repair_node", code_repair_node))

    # 2. Linear ingestion and extraction
    builder.add_edge(START, "ingestion_node")
    builder.add_edge("ingestion_node", "extraction_node")
    builder.add_edge("extraction_node", "feasibility_node")

    # 3. Feasibility refinement conditional routing & loop
    builder.add_conditional_edges(
        "feasibility_node",
        route_feasibility,
        {
            "sequencing_node": "sequencing_node",
            "adaptation_node": "adaptation_node"
        }
    )
    builder.add_edge("adaptation_node", "feasibility_node")

    # 4. Sequencing -> Architecture Specification -> Code Generation -> Evaluation
    builder.add_edge("sequencing_node", "specification_node")
    builder.add_edge("specification_node", "code_generation_node")
    builder.add_edge("code_generation_node", "evaluation_node")

    # 5. Code Evaluation conditional routing & repair loop
    builder.add_conditional_edges(
        "evaluation_node",
        route_evaluation,
        {
            END: END,
            "code_repair_node": "code_repair_node"
        }
    )
    builder.add_edge("code_repair_node", "evaluation_node")

    return builder.compile()


app_workflow = build_pipeline_workflow()
