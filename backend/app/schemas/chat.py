from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class ChatMessageRequest(BaseModel):
    message: Optional[str] = None
    prompt: Optional[str] = None
    text: Optional[str] = None
    content: Optional[str] = None
    paper_id: Optional[str] = None
    model_name: Optional[str] = "qwen2.5-coder:1.5b"

    def get_query_text(self) -> str:
        """Extracts chat prompt text from any provided payload key."""
        return self.message or self.prompt or self.text or self.content or ""


class ChatMessageResponse(BaseModel):
    conversation_id: str
    role: str = "assistant"
    content: str
    thought_process: Optional[str] = None
    timestamp: str


class UserFactRequest(BaseModel):
    fact_text: str
