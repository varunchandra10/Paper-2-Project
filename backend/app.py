import os
import sys
import uuid
import asyncio
import threading
import contextlib
import io
import uvicorn
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

# Add parent directory to path to allow importing from backend
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from pipeline import graph
from utils import detect_gpu, detect_system_ram
import multiprocessing

app = FastAPI(title="Paper-to-Project FastAPI Bridge")

# Enable CORS for Electron frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from core import settings

# Global runs cache
runs = {}

default_constraints = settings.default_constraints
gpu_name = settings.gpu_name
vram_gb = settings.vram_gb
ram_gb = settings.ram_gb
cpu_cores = settings.cpu_cores

class AnalyzeRequest(BaseModel):
    filePath: str
    modelName: str = "qwen2.5-coder:1.5b"

class SSEStreamWriter(io.TextIOBase):
    def __init__(self, callback):
        self.callback = callback
        
    def write(self, s):
        if s.strip():
            self.callback(s.strip())
        return len(s)

def run_pipeline_thread(run_id, pdf_path, model_name, loop, event_queue):
    def send_event(event_type, data):
        # Thread-safe dispatch back to asyncio event loop queue
        loop.call_soon_threadsafe(event_queue.put_nowait, {"event": event_type, "data": data})

    try:
        runs[run_id]["status"] = "running"
        send_event("mascot-state", "reading")
        send_event("log", f"[System] Initializing LangGraph orchestrator on {model_name}...")
        send_event("log", f"[System] Target PDF Path: {pdf_path}")
        send_event("log", f"[System] Detected GPU: {gpu_name} (VRAM: {vram_gb} GB)")
        
        initial_state = {
            "pdf_path": pdf_path,
            "constraints": default_constraints,
            "model_name": model_name
        }

        # Intercept print statements within this execution thread to stream as logs
        def handle_print(text):
            # Send print output as log lines
            send_event("log", text)
            
            # Dynamically map logs to mascot states
            if "Step 1" in text or "Ingestion" in text:
                send_event("mascot-state", "reading")
            elif "Step 2" in text or "Step 3" in text or "Step 4" in text or "Step 5" in text or "Feasibility" in text:
                send_event("mascot-state", "working")
            elif "Step 6" in text or "Report" in text:
                send_event("mascot-state", "idle")

        writer = SSEStreamWriter(handle_print)
        
        with contextlib.redirect_stdout(writer):
            final_state = graph.invoke(initial_state)

        report = final_state.get("report")
        if report and report.markdown_content:
            runs[run_id]["status"] = "completed"
            runs[run_id]["report"] = report.markdown_content
            send_event("mascot-state", "idle")
            send_event("completed", {"report": report.markdown_content})
        else:
            raise Exception("Pipeline completed but returned an empty report.")

    except Exception as e:
        runs[run_id]["status"] = "failed"
        runs[run_id]["error"] = str(e)
        send_event("mascot-state", "sleeping")
        send_event("failed", {"error": str(e)})

@app.post("/analyze")
async def analyze(req: AnalyzeRequest):
    if not os.path.exists(req.filePath):
        raise HTTPException(status_code=404, detail=f"PDF file not found at: {req.filePath}")

    run_id = str(uuid.uuid4())
    event_queue = asyncio.Queue()
    runs[run_id] = {
        "status": "pending",
        "queue": event_queue,
        "report": None,
        "error": None,
        "thread": None
    }

    loop = asyncio.get_running_loop()
    # Start LangGraph blocking invoke in a separate thread
    t = threading.Thread(
        target=run_pipeline_thread,
        args=(run_id, req.filePath, req.modelName, loop, event_queue),
        daemon=True
    )
    runs[run_id]["thread"] = t
    t.start()

    return {"run_id": run_id}

@app.get("/stream/{run_id}")
async def stream(run_id: str):
    if run_id not in runs:
        raise HTTPException(status_code=404, detail="Run ID not found")

    async def event_generator():
        queue = runs[run_id]["queue"]
        while True:
            try:
                event = await queue.get()
                yield event
                # End generation if run enters final state
                if event["event"] in ["completed", "failed"]:
                    break
            except asyncio.CancelledError:
                break

    return EventSourceResponse(event_generator())

@app.get("/status/{run_id}")
def status(run_id: str):
    if run_id not in runs:
        raise HTTPException(status_code=404, detail="Run ID not found")
    
    run = runs[run_id]
    return {
        "status": run["status"],
        "error": run["error"],
        "report": run["report"]
    }

@app.post("/cancel/{run_id}")
def cancel(run_id: str):
    if run_id not in runs:
        raise HTTPException(status_code=404, detail="Run ID not found")
    
    runs[run_id]["status"] = "failed"
    runs[run_id]["error"] = "Cancelled by user"
    return {"status": "cancelled"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
