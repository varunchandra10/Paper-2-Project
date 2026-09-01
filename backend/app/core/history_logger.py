import os
import json
import datetime
from typing import List, Dict, Any, Optional
from app.core.config import settings


def append_conversation_log(conversation_id: str, role: str, message: str):
    """Appends a single chat message to the paper's history log file."""
    log_dir = os.path.join(settings.HISTORY_DIR, "chat_logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{conversation_id}.jsonl")
    
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "role": role,
        "content": message
    }
    
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[HISTORY LOG WARN] Failed to append log for '{conversation_id}': {e}")
