import os
import sys
import json
import uuid
import asyncio
import threading
import contextlib
import io
import uvicorn
from typing import Optional
from fastapi import FastAPI, BackgroundTasks, HTTPException, UploadFile, File, Header
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
import time
from core.logger import log_observability_event

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


# =================================================================
#  PHASE 9: PERSISTENT CHAT & MEMORY DATABASE ROUTING
# =================================================================
from core.database import ChatDatabase
from core.chat_manager import ChatManager

# Global chat database instance (automatically falls back to JSON if PG is down)
db = ChatDatabase()
db.initialize_db()
chat_manager = ChatManager(db)

# --- Schema Models ---
class UserAuthRequest(BaseModel):
    username: str
    password: str

class CreateConversationRequest(BaseModel):
    user_id: str
    title: str
    project_id: str = None

class SaveMessageRequest(BaseModel):
    role: str
    content: str

class RenameConversationRequest(BaseModel):
    title: str

class ChatResponseRequest(BaseModel):
    content: str
    paper_id: str = None

class CreateProjectRequest(BaseModel):
    name: str
    description: str = None

# Global extraction jobs tracking registry
extraction_jobs = {}


# --- API Endpoint Routes ---

@app.post("/users/register")
def register_user(req: UserAuthRequest):
    try:
        user_id = db.add_user(req.username, req.password)
        return {"user_id": user_id, "username": req.username, "status": "registered"}
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@app.post("/users/login")
def login_user(req: UserAuthRequest):
    user_id = db.verify_user(req.username, req.password)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    return {"user_id": user_id, "username": req.username, "status": "authenticated"}

@app.post("/projects")
def create_project(req: CreateProjectRequest):
    try:
        project_id = db.create_project(req.name, req.description)
        return {"project_id": project_id, "status": "created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")

@app.get("/projects")
def list_projects():
    try:
        return db.list_projects()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list projects: {str(e)}")

@app.get("/papers")
def list_papers():
    try:
        return chat_manager.vector_db.list_papers()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list papers: {str(e)}")

@app.get("/papers/{paper_id}")
def get_paper_details(paper_id: str):
    paper = chat_manager.vector_db.get_paper(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found.")
    return paper

@app.get("/extraction/status/{job_id}")
def get_extraction_status(job_id: str):
    if job_id not in extraction_jobs:
        raise HTTPException(status_code=404, detail="Extraction job not found.")
    return extraction_jobs[job_id]

# Set up uploaded papers storage path
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "papers", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

def run_pipeline_in_background(job_id: str, pdf_path: str, constraints: dict, model_name: str, paper_id: str):
    start_time = time.time()
    log_observability_event("extraction_started", paper_id=paper_id, job_id=job_id)
    
    job = extraction_jobs[job_id]
    job["status"] = "running"
    job["logs"].append("EXTRACTION_STARTED")
    job["progress"] = 10
    
    initial_state = {
        "pdf_path": pdf_path,
        "constraints": constraints,
        "model_name": model_name,
        "loop_count": 0,
        "raw_sections": {}
    }
    
    try:
        from pipeline import graph
        # Stream events from LangGraph workflow
        for event in graph.stream(initial_state):
            if not event:
                continue
            node = list(event.keys())[0]
            
            # Map executing graph nodes to streaming SSE logging events
            if node == "ingestion":
                job["logs"].append("SECTION_DETECTED")
                job["logs"].append("RAG_READY")
                job["progress"] = 25
            elif node == "decomposition":
                job["logs"].append("ANALYSIS_STARTED")
                job["progress"] = 45
            elif node == "code_generation":
                job["logs"].append("CODE_GENERATION_STARTED")
                job["progress"] = 75
            elif node in ["static_check", "automated_test", "code_verification"]:
                if "VERIFICATION_STARTED" not in job["logs"]:
                    job["logs"].append("VERIFICATION_STARTED")
                job["progress"] = 90
            elif node == "report":
                job["logs"].append("COMPLETED")
                job["progress"] = 100
                
        # Ensure job is marked completed
        job["status"] = "completed"
        if "COMPLETED" not in job["logs"]:
            job["logs"].append("COMPLETED")
        job["progress"] = 100
        
        latency = (time.time() - start_time) * 1000.0
        log_observability_event("extraction_completed", paper_id=paper_id, job_id=job_id, latency_ms=latency)
    except Exception as e:
        print(f"[BACKGROUND PIPELINE ERROR] Job {job_id} failed: {e}")
        job["status"] = "failed"
        job["error"] = str(e)
        job["logs"].append(f"ERROR: {str(e)}")
        
        latency = (time.time() - start_time) * 1000.0
        log_observability_event("extraction_failed", paper_id=paper_id, job_id=job_id, latency_ms=latency, errors=str(e))

@app.post("/papers/upload")
def upload_paper(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    # Enforce PDF files only by extension
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF documents are supported.")
        
    paper_id = f"paper_{str(uuid.uuid4())[:8]}"
    job_id = f"job_{str(uuid.uuid4())[:8]}"
    
    # Save the file
    upload_path = os.path.join(UPLOAD_DIR, f"{paper_id}.pdf")
    try:
        contents = file.file.read()
        
        # Enforce maximum file size (50MB)
        MAX_SIZE = 50 * 1024 * 1024
        if len(contents) > MAX_SIZE:
            raise HTTPException(status_code=400, detail="File size exceeds maximum limit of 50MB.")
            
        # Validate PDF magic signature bytes
        if not contents.startswith(b"%PDF"):
            raise HTTPException(status_code=400, detail="Invalid PDF file signature.")
            
        with open(upload_path, "wb") as f:
            f.write(contents)
    except HTTPException as http_err:
        raise http_err
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to store PDF file: {str(e)}")
        
    # Register job configuration entry
    extraction_jobs[job_id] = {
        "job_id": job_id,
        "paper_id": paper_id,
        "status": "queued",
        "progress": 0,
        "logs": [],
        "error": None
    }
    
    # Spawn pipeline processing asynchronously
    if background_tasks:
        background_tasks.add_task(
            run_pipeline_in_background,
            job_id=job_id,
            pdf_path=upload_path,
            constraints={"hardware": "RTX 3060", "vram_limit": "12GB"},
            model_name="qwen2.5-coder:1.5b",
            paper_id=paper_id
        )
        
    return {
        "job_id": job_id,
        "paper_id": paper_id,
        "status": "queued"
    }

@app.get("/extraction/stream/{job_id}")
def stream_extraction(job_id: str):
    if job_id not in extraction_jobs:
        raise HTTPException(status_code=404, detail="Extraction job ID not found.")
        
    async def sse_generator():
        job = extraction_jobs[job_id]
        last_index = 0
        while True:
            # Yield any newly appended logs as SSE events
            while last_index < len(job["logs"]):
                log_tag = job["logs"][last_index]
                payload = {
                    "progress": job["progress"],
                    "status": job["status"],
                    "error": job["error"]
                }
                yield f"event: {log_tag}\ndata: {json.dumps(payload)}\n\n"
                last_index += 1
                
            if job["status"] in ["completed", "failed"]:
                break
                
            await asyncio.sleep(0.5)
            
    return StreamingResponse(sse_generator(), media_type="text/event-stream")



@app.post("/conversations")
def create_conversation(req: CreateConversationRequest):
    try:
        conv_id = db.create_conversation(req.user_id, req.title, req.project_id)
        return {"conversation_id": conv_id}
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create conversation: {str(e)}")

@app.get("/conversations")
def list_conversations(user_id: str):
    try:
        return db.list_conversations(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list conversations: {str(e)}")

@app.get("/conversations/{conversation_id}")
def load_conversation(conversation_id: str):
    try:
        messages = db.get_messages(conversation_id)
        summary = db.get_summary(conversation_id)
        return {
            "conversation_id": conversation_id,
            "messages": messages,
            "summary": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load conversation: {str(e)}")

@app.post("/conversations/{conversation_id}/messages")
def save_message(conversation_id: str, req: SaveMessageRequest):
    if req.role not in ["user", "assistant"]:
        raise HTTPException(status_code=400, detail="Role must be either 'user' or 'assistant'.")
    try:
        msg_id = db.save_message(conversation_id, req.role, req.content)
        return {"message_id": msg_id, "status": "saved"}
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save message: {str(e)}")

@app.put("/conversations/{conversation_id}")
def rename_conversation(conversation_id: str, req: RenameConversationRequest):
    try:
        db.rename_conversation(conversation_id, req.title)
        return {"status": "success", "message": "Conversation renamed successfully."}
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to rename conversation: {str(e)}")

@app.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: str):
    try:
        db.delete_conversation(conversation_id)
        return {"status": "success", "message": "Conversation deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete conversation: {str(e)}")

@app.post("/conversations/{conversation_id}/chat")
def conversations_chat(
    conversation_id: str, 
    req: ChatResponseRequest, 
    background_tasks: BackgroundTasks,
    x_user_id: Optional[str] = Header(None)
):
    start_time = time.time()
    
    # Verify the conversation exists and retrieve its owning user_id
    conv_meta = db.get_conversation(conversation_id)
    if not conv_meta:
        raise HTTPException(status_code=404, detail="Conversation session not found.")
        
    # Enforce Day 47 authorization
    if x_user_id and conv_meta["user_id"] != x_user_id:
        raise HTTPException(status_code=403, detail="Unauthorized access to this conversation thread.")
        
    user_id = conv_meta["user_id"]
    
    try:
        # 1. Save incoming user query message
        db.save_message(conversation_id, "user", req.content)
        
        # 2. Add non-blocking background tasks for summarization and memory extraction
        background_tasks.add_task(chat_manager.summarize_conversation_if_needed, conversation_id)
        background_tasks.add_task(chat_manager.extract_and_save_facts, user_id, req.content)
        
        # 3. Compile prompt, classify task, and generate routed response
        reply, model_used = chat_manager.generate_response(conversation_id, user_id, req.content, req.paper_id)
        
        # 4. Save the generated assistant response with the model_used metadata
        db.save_message(conversation_id, "assistant", reply, model_used=model_used)
        
        # Log Day 48 observability metrics
        latency = (time.time() - start_time) * 1000.0
        log_observability_event("chat_completed", conversation_id=conversation_id, model=model_used, latency_ms=latency)
        
        return {"response": reply, "model_used": model_used}
    except Exception as e:
        latency = (time.time() - start_time) * 1000.0
        log_observability_event("chat_failed", conversation_id=conversation_id, latency_ms=latency, errors=str(e))
        raise HTTPException(status_code=500, detail=f"Chat execution failed: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)


