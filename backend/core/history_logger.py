import os
import json
import time
import shutil
from typing import List, Dict, Any, Optional

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONVERSATIONS_DIR = os.path.join(BACKEND_DIR, "papers", "conversations")
FACTS_FILE = os.path.join(CONVERSATIONS_DIR, "facts.json")

os.makedirs(CONVERSATIONS_DIR, exist_ok=True)


def _get_conv_path(conversation_id: str) -> str:
    path = os.path.join(CONVERSATIONS_DIR, conversation_id)
    os.makedirs(path, exist_ok=True)
    return path


def save_conversation_metadata(conversation_id: str, title: str, user_id: str, project_id: Optional[str] = None):
    """Saves conversation title and mappings to metadata.json."""
    conv_dir = _get_conv_path(conversation_id)
    metadata_file = os.path.join(conv_dir, "metadata.json")
    metadata = {
        "conversation_id": conversation_id,
        "title": title,
        "user_id": user_id,
        "project_id": project_id,
        "created_at": time.time()
    }
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)


def get_conversation_metadata(conversation_id: str) -> Optional[Dict[str, Any]]:
    """Reads metadata.json if it exists."""
    metadata_file = os.path.join(CONVERSATIONS_DIR, conversation_id, "metadata.json")
    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None


def append_message_to_jsonl(conversation_id: str, role: str, content: str, model_used: Optional[str] = None) -> str:
    """Appends a new message block to the append-only history.jsonl file."""
    conv_dir = _get_conv_path(conversation_id)
    history_file = os.path.join(conv_dir, "history.jsonl")
    message_id = f"msg_{conversation_id}_{int(time.time() * 1000)}"
    message = {
        "message_id": message_id,
        "timestamp": time.time(),
        "role": role,
        "content": content,
        "model_used": model_used
    }
    with open(history_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(message) + "\n")
    return message_id


def read_conversation_history(conversation_id: str) -> List[Dict[str, Any]]:
    """Reads the chronological conversation transcripts from history.jsonl."""
    history_file = os.path.join(CONVERSATIONS_DIR, conversation_id, "history.jsonl")
    messages = []
    if os.path.exists(history_file):
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        messages.append(json.loads(line.strip()))
        except Exception as e:
            print(f"[LOGGER ERROR] Failed to parse history.jsonl: {e}")
    return messages


def save_summary(conversation_id: str, summary_text: str):
    """Saves condensed context to summary.json."""
    conv_dir = _get_conv_path(conversation_id)
    summary_file = os.path.join(conv_dir, "summary.json")
    summary = {
        "conversation_id": conversation_id,
        "last_updated": time.time(),
        "summary": summary_text
    }
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)


def read_summary(conversation_id: str) -> Optional[str]:
    """Reads rolling summary from summary.json."""
    summary_file = os.path.join(CONVERSATIONS_DIR, conversation_id, "summary.json")
    if os.path.exists(summary_file):
        try:
            with open(summary_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("summary")
        except Exception:
            pass
    return None


def list_conversations(user_id: str) -> List[Dict[str, Any]]:
    """Scans all folders and returns metadata filtered by user_id."""
    conversations = []
    if not os.path.exists(CONVERSATIONS_DIR):
        return conversations

    for folder_name in os.listdir(CONVERSATIONS_DIR):
        folder_path = os.path.join(CONVERSATIONS_DIR, folder_name)
        if os.path.isdir(folder_path):
            metadata = get_conversation_metadata(folder_name)
            if metadata and metadata.get("user_id") == user_id:
                conversations.append(metadata)
    
    # Sort by creation time (newest first)
    conversations.sort(key=lambda x: x.get("created_at", 0), reverse=True)
    return conversations


def rename_conversation(conversation_id: str, title: str):
    """Updates the title inside metadata.json."""
    metadata = get_conversation_metadata(conversation_id)
    if metadata:
        metadata["title"] = title
        metadata_file = os.path.join(CONVERSATIONS_DIR, conversation_id, "metadata.json")
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
    else:
        raise ValueError("Conversation not found.")


def delete_conversation(conversation_id: str):
    """Recursively deletes conversation directory from disk."""
    folder_path = os.path.join(CONVERSATIONS_DIR, conversation_id)
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)


def add_memory_fact(user_id: str, fact: str, category: str):
    """Saves user preference fact to facts.json flat file."""
    data = {}
    if os.path.exists(FACTS_FILE):
        try:
            with open(FACTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            pass

    if user_id not in data:
        data[user_id] = []

    # Avoid duplicate facts
    existing_facts = [f["fact"].lower().strip() for f in data[user_id]]
    if fact.lower().strip() not in existing_facts:
        data[user_id].append({
            "fact": fact.strip(),
            "category": category.strip(),
            "timestamp": time.time()
        })

        with open(FACTS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)


def get_memory_facts(user_id: str) -> List[Dict[str, Any]]:
    """Reads facts.json list for target user_id."""
    if os.path.exists(FACTS_FILE):
        try:
            with open(FACTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get(user_id, [])
        except Exception:
            pass
    return []
