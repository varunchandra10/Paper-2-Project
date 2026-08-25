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
def conversations_chat(conversation_id: str, req: ChatResponseRequest, background_tasks: BackgroundTasks):
    # Verify the conversation exists and retrieve its owning user_id
    conv_meta = db.get_conversation(conversation_id)
    if not conv_meta:
        raise HTTPException(status_code=404, detail="Conversation session not found.")
        
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
        
        return {"response": reply, "model_used": model_used}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat execution failed: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)


