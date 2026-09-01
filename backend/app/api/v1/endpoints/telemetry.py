from fastapi import APIRouter
from app.core.tracer import AgentTracer
from app.evals.eval_suite import run_reliability_benchmark

router = APIRouter()
tracer = AgentTracer()


@router.get("/history/{paper_id}/traces")
def get_paper_traces(paper_id: str):
    """Serves agent execution telemetry trace log timeline."""
    traces = tracer.get_traces(paper_id)
    return {"paper_id": paper_id, "traces": traces}


@router.get("/evals/benchmark/{paper_id}")
def get_reliability_benchmark(paper_id: str):
    """Serves Reliability Scorecard (Reliability = Observability + Evals)."""
    scorecard = run_reliability_benchmark(paper_id)
    return scorecard
