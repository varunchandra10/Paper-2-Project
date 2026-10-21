import os
import json
import uuid
import asyncio
from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
from app.core.config import settings
from app.core.database import ChatDatabase
from app.core.job_store import get_job_store, JobStoreDictWrapper, JobStatus
from app.core.events import EventTypes, emit_event
from app.graph.workflow import app_workflow
from app.schemas.pipeline import ParameterApprovalRequest

router = APIRouter()
db = ChatDatabase()
db.initialize_db()

job_store = get_job_store()
analysis_jobs = JobStoreDictWrapper(job_store)


@router.get("/pipeline/jobs/{run_id}/events")
@router.get("/pipeline/stream/{run_id}")
@router.get("/stream/{run_id}")
@router.get("/extraction/stream/{run_id}")
async def stream_analysis_events(run_id: str, request: Request, since_id: int = 0):
    """
    Phase 9: Server-Sent Events (SSE) stream endpoint for truthful, event-driven live telemetry.
    Supports reconnection and idempotent catch-up via Last-Event-ID header or since_id parameter.
    """
    header_last_id = request.headers.get("Last-Event-ID")
    last_seen_id = int(header_last_id) if header_last_id and header_last_id.isdigit() else since_id

    async def event_generator():
        nonlocal last_seen_id
        yield "event: log\ndata: [System] Connected to event-driven analysis telemetry stream.\n\n"
        await asyncio.sleep(0.05)

        for iteration in range(240):  # 2 minutes max stream duration
            # 1. Fetch new events from persistent SQLite event log
            new_events = job_store.get_events(run_id, since_id=last_seen_id)
            for ev in new_events:
                eid = ev["event_id"]
                last_seen_id = max(last_seen_id, eid)
                payload = json.dumps(ev)

                # Emit primary structured event with ID for reconnect replay
                yield f"id: {eid}\nevent: {ev['event']}\ndata: {payload}\n\n"

                # Also emit backward-compatible milestone events for frontend EventSource listeners
                node = ev.get("node")
                if ev["event"] == EventTypes.NODE_COMPLETED:
                    if node == "ingestion_node":
                        yield f"id: {eid}\nevent: SECTION_DETECTED\ndata: {payload}\n\n"
                    elif node == "extraction_node":
                        yield f"id: {eid}\nevent: RAG_READY\ndata: {payload}\n\n"
                        yield f"id: {eid}\nevent: ANALYSIS_STARTED\ndata: {payload}\n\n"
                    elif node == "code_generation_node":
                        yield f"id: {eid}\nevent: CODE_GENERATION_STARTED\ndata: {payload}\n\n"
                    elif node == "evaluation_node":
                        yield f"id: {eid}\nevent: VERIFICATION_STARTED\ndata: {payload}\n\n"

                # Emit mascot state dynamically based on actual node execution
                mascot = ev.get("metadata", {}).get("mascot_state")
                if mascot:
                    yield f"event: mascot-state\ndata: {mascot}\n\n"

                # Terminal completion event
                if ev["event"] in (EventTypes.PIPELINE_COMPLETED, "COMPLETED"):
                    yield f"id: {eid}\nevent: COMPLETED\ndata: {payload}\n\n"
                    yield f"id: {eid}\nevent: completed\ndata: {payload}\n\n"
                    yield "event: mascot-state\ndata: ready\n\n"
                    return

                # Terminal failure event
                if ev["event"] in (EventTypes.PIPELINE_FAILED, EventTypes.ERROR, "FAILED"):
                    yield f"id: {eid}\nevent: ERROR\ndata: {payload}\n\n"
                    yield f"id: {eid}\nevent: failed\ndata: {payload}\n\n"
                    yield "event: mascot-state\ndata: sleeping\n\n"
                    return

            # Check job terminal status directly if no events arrived
            job = job_store.get_job(run_id)
            if job and job.status in JobStatus.TERMINAL_STATUSES:
                term_payload = json.dumps({
                    "status": job.status,
                    "progress": job.progress,
                    "paper_id": job.paper_id,
                    "job_id": job.job_id,
                    "result": job.result,
                    "error": job.error
                })
                if job.status == JobStatus.COMPLETED:
                    yield f"event: COMPLETED\ndata: {term_payload}\n\n"
                    yield "event: mascot-state\ndata: ready\n\n"
                elif job.status == JobStatus.FAILED:
                    yield f"event: ERROR\ndata: {term_payload}\n\n"
                    yield "event: mascot-state\ndata: sleeping\n\n"
                elif job.status == JobStatus.CANCELLED:
                    yield f"event: CANCELLED\ndata: {term_payload}\n\n"
                    yield "event: mascot-state\ndata: sleeping\n\n"
                return

            # Keepalive ping
            if iteration % 10 == 0:
                cur_prog = job.progress if job else 0.0
                cur_stat = job.status if job else "unknown"
                yield f": keepalive\nevent: ping\ndata: {{\"status\": \"{cur_stat}\", \"progress\": {cur_prog}, \"last_event_id\": {last_seen_id}}}\n\n"

            await asyncio.sleep(0.5)

        # Timeout reached
        yield f"event: STILL_RUNNING\ndata: {{\"status\": \"running\", \"job_id\": \"{run_id}\"}}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


class AnalyzeRequest(BaseModel):
    paper_id: str
    constraints: Optional[dict] = None
    model_name: Optional[str] = settings.DEFAULT_MODEL


def run_pipeline_task(job_id: str, paper_id: str, constraints: dict, model_name: str):
    """Executes StateGraph pipeline asynchronously in background with truthful event telemetry."""
    if job_store.is_cancellation_requested(job_id):
        job_store.fail_job(job_id, error="Job execution cancelled prior to start")
        emit_event(job_id, paper_id, EventTypes.PIPELINE_FAILED, node_name="pipeline", status="cancelled", metadata={"error": "Cancelled prior to start"})
        return

    # Emit truthful pipeline start event
    emit_event(job_id, paper_id, EventTypes.PIPELINE_STARTED, node_name="pipeline", progress=5.0, status="running")
    pdf_path = os.path.join(settings.PAPERS_DIR, f"{paper_id}.pdf")
    if not os.path.exists(pdf_path):
        pdf_path = os.path.join(settings.BASE_DIR, f"{paper_id}.pdf")

    try:
        initial_state = {
            "job_id": job_id,
            "paper_id": paper_id,
            "pdf_path": pdf_path,
            "constraints": constraints or {"max_vram_gb": 6.0},
            "model_name": model_name,
            "loop_count": 0
        }

        if job_store.is_cancellation_requested(job_id):
            return

        # Execute the telemetry-wrapped LangGraph StateGraph
        final_state = app_workflow.invoke(initial_state)

        if job_store.is_cancellation_requested(job_id):
            return

        # Save output JSON
        json_path = os.path.join(settings.EXTRACTED_JSON_DIR, f"{paper_id}.json")
        out_data = {
            "paper_id": paper_id,
            "metadata": final_state["paper_doc"].metadata.model_dump() if final_state.get("paper_doc") and hasattr(final_state["paper_doc"].metadata, "model_dump") else {},
            "extracted_parameters": final_state["extracted_parameters"].model_dump() if final_state.get("extracted_parameters") and hasattr(final_state["extracted_parameters"], "model_dump") else {},
            "feasibility_report": final_state["feasibility_report"].model_dump() if final_state.get("feasibility_report") and hasattr(final_state["feasibility_report"], "model_dump") else {},
            "build_sequence": final_state["build_sequence"].model_dump() if final_state.get("build_sequence") and hasattr(final_state["build_sequence"], "model_dump") else {},
            "report": final_state.get("report", {}),
            "parameters_approved": final_state.get("parameters_approved", True)
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(out_data, f, indent=2, default=str)

        # Update and save knowledge graph with extracted parameters & modules
        try:
            from app.retrieval.knowledge_graph import PaperKnowledgeGraph
            kg = PaperKnowledgeGraph()
            kg.paper_id = paper_id
            kg.build_from_canonical(out_data.get("canonical_document") or out_data, paper_id=paper_id)
        except Exception as kg_err:
            print(f"[PIPELINE WARN] Failed to build knowledge graph for '{job_id}': {kg_err}")

        # Generate & save Phase 10 Reproducibility Run Manifest
        try:
            from app.core.manifest import generate_run_manifest
            manifest = generate_run_manifest(
                run_id=job_id,
                paper_id=paper_id,
                pdf_path=pdf_path,
                model_name=model_name,
                temperature=0.0,
                execution_summary={
                    "status": "COMPLETED",
                    "parameters_extracted": len(out_data.get("extracted_parameters", {})),
                    "feasibility_status": out_data.get("feasibility_report", {}).get("overall_status", "UNKNOWN")
                }
            )
            out_data["run_manifest"] = manifest.model_dump()
        except Exception as man_err:
            print(f"[PIPELINE WARN] Failed to generate run manifest for '{job_id}': {man_err}")

        job_store.complete_job(job_id, result=out_data)
        emit_event(job_id, paper_id, EventTypes.PIPELINE_COMPLETED, node_name="pipeline", progress=100.0, status="success", metadata={"output_file": json_path})
    except Exception as e:
        job_store.fail_job(job_id, error=str(e))
        emit_event(job_id, paper_id, EventTypes.PIPELINE_FAILED, node_name="pipeline", status="failed", metadata={"error": str(e)})


@router.post("/pipeline/analyze")
@router.post("/analyze")
def trigger_analysis(req: AnalyzeRequest, bg: BackgroundTasks):
    """Triggers asynchronous analysis job with duplicate-submission protection."""
    active_job = job_store.get_active_job_for_paper(req.paper_id)
    if active_job:
        return {
            "job_id": active_job.job_id,
            "paper_id": active_job.paper_id,
            "status": active_job.status,
            "message": "Analysis already in progress for this paper"
        }

    job = job_store.create_job(
        paper_id=req.paper_id,
        initial_stage="queued",
        progress=0.0,
        status=JobStatus.QUEUED
    )
    bg.add_task(run_pipeline_task, job.job_id, req.paper_id, req.constraints or {}, req.model_name or settings.DEFAULT_MODEL)
    return {"job_id": job.job_id, "paper_id": req.paper_id, "status": "queued"}


@router.post("/history/{paper_id}/trigger_analysis")
def trigger_analysis_legacy(paper_id: str, bg: BackgroundTasks, model_name: Optional[str] = None):
    """Route alias supporting /history/{paper_id}/trigger_analysis."""
    req = AnalyzeRequest(paper_id=paper_id, model_name=model_name or settings.DEFAULT_MODEL)
    return trigger_analysis(req, bg)


@router.get("/pipeline/jobs/{job_id}")
@router.get("/pipeline/jobs/{job_id}/status")
@router.get("/analyze/{job_id}/status")
@router.get("/extraction/status/{job_id}")
def get_job_status(job_id: str):
    """Returns status and progress of an active or completed analysis job."""
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job ID not found.")
    return job.to_dict()


@router.post("/pipeline/jobs/{job_id}/cancel")
@router.post("/analyze/{job_id}/cancel")
def cancel_analysis_job(job_id: str):
    """Cancels an active analysis job."""
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job ID not found.")
    success = job_store.cancel_job(job.job_id)
    return {
        "job_id": job.job_id,
        "paper_id": job.paper_id,
        "cancelled": success,
        "status": JobStatus.CANCELLED if success else job.status
    }


@router.post("/papers/{paper_id}/approve_parameters")
@router.post("/pipeline/papers/{paper_id}/approve_parameters")
@router.post("/history/{paper_id}/approve_parameters")
def approve_parameters(paper_id: str, req: ParameterApprovalRequest):
    """Saves user-defined parameter overrides and records episodic memory."""
    json_path = os.path.join(settings.EXTRACTED_JSON_DIR, f"{paper_id}.json")
    if not os.path.exists(json_path):
        raise HTTPException(status_code=404, detail="Paper extracted JSON state not found.")
        
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            state_data = json.load(f)
            
        ext_params = state_data.get("extracted_parameters", {})
        for k, v in req.custom_parameters.items():
            if k in ext_params and isinstance(ext_params[k], dict):
                ext_params[k]["value"] = v
                ext_params[k]["status"] = "USER_DEFINED"
            else:
                ext_params[k] = {"value": v, "status": "USER_DEFINED", "confidence": 100}
                
        state_data["extracted_parameters"] = ext_params
        state_data["parameters_approved"] = True
        
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(state_data, f, indent=2, default=str)
            
        # Save episodic run memory into database
        title = state_data.get("metadata", {}).get("title", paper_id)
        db.save_episodic_run(paper_id=paper_id, paper_title=title, hyperparameters=req.custom_parameters)
        
        # Create completion job entry to satisfy frontend SSE and status tracking
        job = job_store.create_job(
            paper_id=paper_id,
            initial_stage="parameters_approved",
            progress=100.0,
            status=JobStatus.COMPLETED
        )
        job_store.complete_job(job.job_id, result={"action": "approve_parameters", "paper_id": paper_id})

        return {
            "job_id": job.job_id,
            "status": "completed",
            "message": "Parameters approved and episodic memory saved.",
            "paper_id": paper_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to approve parameters: {str(e)}")


@router.get("/pipeline/jobs/{run_id}/manifest")
@router.get("/manifest/{run_id}")
@router.get("/pipeline/manifest/{run_id}")
def get_run_manifest_endpoint(run_id: str):
    """Phase 10: Retrieves the immutable execution manifest for an analysis run."""
    from app.core.manifest import get_manifest
    manifest = get_manifest(run_id)
    if not manifest:
        raise HTTPException(status_code=404, detail=f"No run manifest found for run_id '{run_id}'.")
    return manifest


@router.get("/manifest/{run_id}/explain")
@router.get("/pipeline/manifest/{run_id}/explain")
def explain_run_endpoint(run_id: str):
    """
    Phase 10 Exit Criteria Endpoint:
    Reconstructs an analysis run and provides an auditable explanation of its configuration and results.
    """
    from app.core.manifest import explain_run
    explanation = explain_run(run_id)
    if explanation.get("status") == "NOT_FOUND":
        raise HTTPException(status_code=404, detail=f"No run manifest found for run_id '{run_id}'.")
    return explanation


@router.get("/manifests")
@router.get("/pipeline/manifests")
def list_manifests_endpoint(limit: int = 100):
    """Lists all stored execution run manifests ordered by recency."""
    from app.core.manifest import list_manifests
    return list_manifests(limit=limit)
