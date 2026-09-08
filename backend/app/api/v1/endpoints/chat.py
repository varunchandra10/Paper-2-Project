import uuid
import asyncio
from typing import Optional
from fastapi import APIRouter, HTTPException, Request
from sse_starlette.sse import EventSourceResponse
from app.schemas.chat import ChatMessageRequest, UserFactRequest
from app.agents.chat_agent import ChatAgent
from app.core.database import ChatDatabase

router = APIRouter()
chat_agent = ChatAgent()
db = ChatDatabase()
db.initialize_db()


@router.get("/conversations")
def list_conversations(user_id: Optional[str] = None):
    """Returns system-wide conversations for local desktop application instance along with active_conversation_id."""
    convs = db.get_all_conversations()
    active_id = db.get_active_conversation_id()
    return {"conversations": convs, "active_conversation_id": active_id}


@router.get("/conversations/active")
def get_active_conversation():
    """Returns metadata and messages for the currently active conversation."""
    active_id = db.get_active_conversation_id()
    if not active_id:
        return {"active_conversation_id": None, "conversation": None}
    conv_data = db._load_conversation_file(active_id)
    project_id = conv_data.get("project_id") or conv_data.get("paper_id")
    paper_title = db.get_paper_title_by_id_or_name(project_id, None)
    raw_title = conv_data.get("title", "")
    is_generic = not raw_title or raw_title.startswith("conv_") or raw_title in ["New Research Analysis", "Untitled Thread", "Research Thread"]
    title = raw_title if not is_generic else (paper_title or "New Research Analysis")
    return {
        "active_conversation_id": active_id,
        "id": active_id,
        "title": title,
        "project_id": project_id,
        "messages": conv_data.get("messages", [])
    }


@router.post("/conversations/active")
def set_active_conversation(req: dict):
    """Explicitly updates or clears the active conversation ID on the backend."""
    conv_id = req.get("conversation_id")
    db.set_active_conversation_id(conv_id)
    return {"status": "success", "active_conversation_id": conv_id}


@router.post("/conversations")
def create_conversation(req: Optional[dict] = None):
    """Creates a new conversation thread with human title."""
    conv_id = f"conv_{str(uuid.uuid4())[:8]}"
    project_id = (req and (req.get("project_id") or req.get("paper_id")))
    title = (req and req.get("title")) or "New Research Analysis"
    if title.startswith("conv_"):
        title = "New Research Analysis"
    conv_data = db._load_conversation_file(conv_id)
    conv_data["title"] = title
    if project_id:
        conv_data["project_id"] = project_id
    db._save_conversation_file(conv_id, conv_data)
    db.set_active_conversation_id(conv_id)
    return {"conversation_id": conv_id, "id": conv_id, "title": title, "project_id": project_id}


@router.post("/conversations/{conversation_id}/chat")
async def post_chat_message(conversation_id: str, req: ChatMessageRequest):
    """Processes user chat prompt using ChatAgent (ReACT framework & diagnostic tools).

    Runs the blocking ReACT inference loop inside a thread pool via asyncio.to_thread so
    the uvicorn event loop is never blocked during the 10–30s model inference call.
    Other API requests (e.g. /conversations, /status) remain responsive throughout.
    """
    db.set_active_conversation_id(conversation_id)
    query_text = req.get_query_text()
    res = await asyncio.to_thread(
        chat_agent.process_message,
        conversation_id=conversation_id,
        query=query_text,
        paper_id=req.paper_id,
        model_name=req.model_name
    )
    return res


@router.post("/conversations/{conversation_id}/chat/stream")
async def stream_chat_message(conversation_id: str, req: ChatMessageRequest, request: Request):
    """Streams the ChatAgent ReACT response as Server-Sent Events (SSE).

    Event protocol:
      event: status      — progress status text ("Thinking...", "ReACT turn 1/3...")
      event: thought     — ReACT THOUGHT trace
      event: action      — tool call being executed
      event: observation — tool result summary
      event: token       — individual answer word/chunk (assemble client-side)
      event: done        — JSON payload with title, model_used, thought, action, observation
      event: error       — error message string

    Client disconnects are handled gracefully via asyncio.CancelledError.
    """
    db.set_active_conversation_id(conversation_id)
    query_text = req.get_query_text()

    async def event_generator():
        async for chunk in chat_agent.process_message_stream(
            conversation_id=conversation_id,
            query=query_text,
            paper_id=req.paper_id,
            model_name=req.model_name
        ):
            # Check if client disconnected between chunks
            if await request.is_disconnected():
                break
            yield chunk

    return EventSourceResponse(event_generator())


@router.get("/conversations/{conversation_id}")
@router.get("/conversations/{conversation_id}/messages")
def get_chat_history(conversation_id: str):
    """Returns past conversation messages along with current conversation metadata."""
    db.set_active_conversation_id(conversation_id)
    conv_data = db._load_conversation_file(conversation_id)
    msgs = conv_data.get("messages", [])
    raw_title = conv_data.get("title", "")
    project_id = conv_data.get("project_id") or conv_data.get("paper_id")
    paper_title = db.get_paper_title_by_id_or_name(project_id, None)
    is_generic = not raw_title or raw_title.startswith("conv_") or raw_title in ["New Research Analysis", "Untitled Thread", "Research Thread"]
    title = raw_title if not is_generic else (paper_title or "New Research Analysis")
    return {
        "conversation_id": conversation_id,
        "id": conversation_id,
        "title": title,
        "project_id": project_id,
        "messages": msgs
    }


@router.patch("/conversations/{conversation_id}")
def update_conversation(conversation_id: str, req: dict):
    """Updates conversation properties such as title."""
    title = req.get("title")
    if not title or not str(title).strip():
        raise HTTPException(status_code=400, detail="Title cannot be empty")
    clean_title = str(title).strip()
    success = db.update_conversation_title(conversation_id, clean_title)
    if not success:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"status": "success", "conversation_id": conversation_id, "title": clean_title}


@router.delete("/conversations/{conversation_id}")
def delete_conversation_thread(conversation_id: str):
    """Deletes conversation thread file from disk."""
    success = db.delete_conversation(conversation_id)
    return {"status": "deleted" if success else "not_found", "conversation_id": conversation_id}


@router.get("/memory")
def get_user_memory(conversation_id: str = "global"):
    """Returns stored user facts."""
    facts = db.get_user_facts(conversation_id)
    return {"conversation_id": conversation_id, "facts": facts}


@router.post("/memory")
def add_user_memory(req: UserFactRequest, conversation_id: str = "global"):
    """Adds a new user fact memory."""
    db.save_memory_fact(req.fact_text, conversation_id=conversation_id)
    return {"message": "User fact memory saved.", "fact": req.fact_text}
