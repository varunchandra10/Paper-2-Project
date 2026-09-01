import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException
from app.schemas.chat import ChatMessageRequest, UserFactRequest
from app.agents.chat_agent import ChatAgent
from app.core.database import ChatDatabase

router = APIRouter()
chat_agent = ChatAgent()
db = ChatDatabase()
db.initialize_db()


@router.get("/conversations")
def list_conversations(user_id: Optional[str] = None):
    """Returns system-wide conversations for local desktop application instance."""
    convs = db.get_all_conversations()
    return {"conversations": convs}


@router.post("/conversations")
def create_conversation(req: Optional[dict] = None):
    """Creates a new conversation thread with human title."""
    conv_id = f"conv_{str(uuid.uuid4())[:8]}"
    title = (req and req.get("title")) or "New Research Analysis"
    if title.startswith("conv_"):
        title = "New Research Analysis"
    conv_data = db._load_conversation_file(conv_id)
    conv_data["title"] = title
    db._save_conversation_file(conv_id, conv_data)
    db.save_message(conv_id, "assistant", "Hello! How can I assist with your paper analysis?")
    return {"conversation_id": conv_id, "id": conv_id, "title": title}


@router.post("/conversations/{conversation_id}/chat")
def post_chat_message(conversation_id: str, req: ChatMessageRequest):
    """Processes user chat prompt using ChatAgent (ReACT framework & diagnostic tools)."""
    query_text = req.get_query_text()
    res = chat_agent.process_message(
        conversation_id=conversation_id,
        query=query_text,
        paper_id=req.paper_id,
        model_name=req.model_name
    )
    return res


@router.get("/conversations/{conversation_id}")
@router.get("/conversations/{conversation_id}/messages")
def get_chat_history(conversation_id: str):
    """Returns past conversation messages."""
    msgs = db.get_messages(conversation_id)
    return {"conversation_id": conversation_id, "messages": msgs}


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
