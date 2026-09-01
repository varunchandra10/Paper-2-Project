import os
import json
import uuid
import asyncio
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
from app.core.config import settings
from app.core.database import ChatDatabase
from app.graph.workflow import app_workflow
from app.schemas.pipeline import ParameterApprovalRequest

router = APIRouter()
db = ChatDatabase()
db.initialize_db()

analysis_jobs: Dict[str, dict] = {}


@router.get("/stream/{run_id}")
@router.get("/extraction/stream/{run_id}")
async def stream_analysis_events(run_id: str):
    """Server-Sent Events (SSE) stream endpoint for live analysis progress & mascot state."""
    async def event_generator():
        yield "event: log\ndata: [System] Connected to analysis telemetry stream.\n\n"
        yield "event: mascot-state\ndata: working\n\n"
        
        # Check job state
        for _ in range(5):
            await asyncio.sleep(1.0)
            if run_id in analysis_jobs:
                job = analysis_jobs[run_id]
                status = job.get("status")
                if status == "completed":
                    yield "event: completed\ndata: {\"status\": \"completed\"}\n\n"
                    yield "event: mascot-state\ndata: ready\n\n"
                    break
                elif status == "failed":
                    err = job.get("error", "Unknown error")
                    yield f"event: failed\ndata: {{\"error\": \"{err}\"}}\n\n"
                    yield "event: mascot-state\ndata: sleeping\n\n"
                    break

        yield "event: completed\ndata: {\"status\": \"finished\"}\n\n"
        yield "event: mascot-state\ndata: ready\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


class AnalyzeRequest(BaseModel):
    paper_id: str
    constraints: Optional[dict] = None
    model_name: Optional[str] = settings.DEFAULT_MODEL


def run_pipeline_task(job_id: str, paper_id: str, constraints: dict, model_name: str):
    """Executes StateGraph pipeline asynchronously in background."""
    analysis_jobs[job_id]["status"] = "processing"
    pdf_path = os.path.join(settings.PAPERS_DIR, f"{paper_id}.pdf")
    if not os.path.exists(pdf_path):
        pdf_path = os.path.join(settings.BASE_DIR, f"{paper_id}.pdf")
        
    try:
        initial_state = {
            "pdf_path": pdf_path,
            "constraints": constraints or {"max_vram_gb": 6.0},
            "model_name": model_name,
            "loop_count": 0
        }
        final_state = app_workflow.invoke(initial_state)
        
        # Save output JSON
        json_path = os.path.join(settings.EXTRACTED_JSON_DIR, f"{paper_id}.json")
        out_data = {
            "paper_id": paper_id,
            "metadata": final_state["paper_doc"].metadata.model_dump(),
            "extracted_parameters": final_state["extracted_parameters"].model_dump(),
            "feasibility_report": final_state["feasibility_report"].model_dump(),
            "build_sequence": final_state["build_sequence"].model_dump(),
            "report": final_state.get("report", {}),
            "parameters_approved": final_state.get("parameters_approved", True)
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(out_data, f, indent=2, default=str)
            
        analysis_jobs[job_id]["status"] = "completed"
        analysis_jobs[job_id]["progress"] = 100
    except Exception as e:
        analysis_jobs[job_id]["status"] = "failed"
        analysis_jobs[job_id]["error"] = str(e)


@router.post("/analyze")
def trigger_analysis(req: AnalyzeRequest, bg: BackgroundTasks):
    job_id = f"job_{str(uuid.uuid4())[:8]}"
    analysis_jobs[job_id] = {
        "job_id": job_id,
        "paper_id": req.paper_id,
        "status": "queued",
        "progress": 20
    }
    bg.add_task(run_pipeline_task, job_id, req.paper_id, req.constraints or {}, req.model_name or settings.DEFAULT_MODEL)
    return {"job_id": job_id, "status": "queued"}


@router.get("/analyze/{job_id}/status")
def get_job_status(job_id: str):
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Job ID not found.")
    return analysis_jobs[job_id]


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
        
        return {"message": "Parameters approved and episodic memory saved.", "paper_id": paper_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to approve parameters: {str(e)}")
