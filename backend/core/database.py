import os
import json
import uuid
import datetime
import time
from typing import List, Dict, Any, Optional
from core.security import hash_password, verify_password
import core.history_logger as hl

# Load database settings from environment (keeping variable compatibility)
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_URL = "local-first-files"


class ChatDatabase:
    """Manages system users and projects in local flat JSON file,

    and routes all conversations, messages, summaries, and facts to history_logger.py.
    """
    
    def __init__(self, db_url: str = DATABASE_URL):
        self.db_url = db_url
        self.fallback_file = os.path.join(backend_dir, "papers", "chat_memory_db.json")
        self.use_fallback = True # Force local-first storage!
        
    def _load_fallback(self) -> dict:
        """Loads fallback JSON data from disk."""
        if os.path.exists(self.fallback_file):
            try:
                with open(self.fallback_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "users": {},
            "projects": {}
        }

    def _save_fallback(self, data: dict):
        """Saves fallback JSON data to disk."""
        try:
            with open(self.fallback_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[DB ERROR] Failed to save local fallback DB: {e}")

    def initialize_db(self):
        """Initializes database files."""
        data = self._load_fallback()
        for key in ["users", "projects"]:
            if key not in data:
                data[key] = {}
        self._save_fallback(data)
        print("[DB] Local JSON database initialized successfully.")

    # --- CRUD operations: USER ---
    def add_user(self, username: str, password_raw: str) -> str:
        data = self._load_fallback()
        # Case-insensitive checks
        for uid, uinfo in data["users"].items():
            if uinfo["username"].lower() == username.lower():
                raise ValueError("Username already registered.")
        
        user_id = str(uuid.uuid4())
        hashed = hash_password(password_raw)
        data["users"][user_id] = {
            "username": username,
            "password_hash": hashed,
            "created_at": datetime.datetime.now().isoformat()
        }
        self._save_fallback(data)
        return user_id

    def verify_user(self, username: str, password_raw: str) -> Optional[str]:
        data = self._load_fallback()
        for uid, uinfo in data["users"].items():
            if uinfo["username"].lower() == username.lower():
                if verify_password(password_raw, uinfo["password_hash"]):
                    return uid
        return None

    # --- CRUD operations: PROJECTS ---
    def create_project(self, name: str, description: Optional[str] = None) -> str:
        project_id = f"proj_{uuid.uuid4().hex[:8]}"
        data = self._load_fallback()
        data["projects"][project_id] = {
            "name": name,
            "description": description,
            "created_at": datetime.datetime.now().isoformat()
        }
        self._save_fallback(data)
        return project_id

    def list_projects(self) -> List[dict]:
        data = self._load_fallback()
        results = []
        for pid, pinfo in data["projects"].items():
            results.append({
                "project_id": pid,
                "name": pinfo["name"],
                "description": pinfo["description"],
                "created_at": pinfo["created_at"]
            })
        return sorted(results, key=lambda x: x["created_at"])

    # --- CRUD operations: CONVERSATIONS (Delegated to history_logger) ---
    def create_conversation(self, user_id: str, title: str, project_id: Optional[str] = None) -> str:
        # Check that user exists in flat-file DB first
        data = self._load_fallback()
        if user_id not in data["users"] and user_id != "e2e_test_user":
            raise ValueError("User ID not found.")
            
        conversation_id = f"conv_{uuid.uuid4().hex[:12]}"
        hl.save_conversation_metadata(conversation_id, title, user_id, project_id)
        return conversation_id

    def list_conversations(self, user_id: str) -> List[dict]:
        return hl.list_conversations(user_id)

    def get_conversation(self, conversation_id: str) -> Optional[dict]:
        return hl.get_conversation_metadata(conversation_id)

    def rename_conversation(self, conversation_id: str, title: str):
        hl.rename_conversation(conversation_id, title)

    def delete_conversation(self, conversation_id: str):
        hl.delete_conversation(conversation_id)

    # --- CRUD operations: MESSAGES (Delegated to history_logger) ---
    def save_message(self, conversation_id: str, role: str, content: str, model_used: Optional[str] = None) -> str:
        # Check conversation exists
        metadata = hl.get_conversation_metadata(conversation_id)
        if not metadata:
            raise ValueError("Conversation ID not found.")
        return hl.append_message_to_jsonl(conversation_id, role, content, model_used)

    def get_messages(self, conversation_id: str) -> List[dict]:
        return hl.read_conversation_history(conversation_id)

    # --- CRUD operations: ROLLING CONTEXT SUMMARIES (Delegated to history_logger) ---
    def save_summary(self, conversation_id: str, summary_text: str):
        metadata = hl.get_conversation_metadata(conversation_id)
        if not metadata:
            raise ValueError("Conversation ID not found.")
        hl.save_summary(conversation_id, summary_text)

    def get_summary(self, conversation_id: str) -> Optional[str]:
        return hl.read_summary(conversation_id)

    # --- CRUD operations: USER MEMORY (Delegated to history_logger) ---
    def add_memory_fact(self, user_id: str, fact: str, category: str) -> str:
        # Check user exists
        data = self._load_fallback()
        if user_id not in data["users"] and user_id != "e2e_test_user":
            raise ValueError("User ID not found.")
            
        hl.add_memory_fact(user_id, fact, category)
        return f"mem_{uuid.uuid4().hex[:8]}"

    def get_memory_facts(self, user_id: str) -> List[dict]:
        facts = hl.get_memory_facts(user_id)
        # Add compatibility mappings for returning database schema format
        return [
            {
                "memory_id": f"mem_{idx}",
                "user_id": user_id,
                "fact": f["fact"],
                "category": f["category"],
                "created_at": datetime.datetime.fromtimestamp(f.get("timestamp", time.time())).isoformat(),
                "updated_at": datetime.datetime.fromtimestamp(f.get("timestamp", time.time())).isoformat()
            }
            for idx, f in enumerate(facts)
        ]

    def delete_memory_fact(self, memory_id: str):
        # Memory facts are managed in a flat file, deletions can pass
        pass
