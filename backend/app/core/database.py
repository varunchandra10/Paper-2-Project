import os
import threading
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.core.db.storage_engine import StorageEngine
from app.core.db.chat_repo import ChatRepository
from app.core.db.profile_repo import ProfileRepository
from app.core.db.paper_repo import PaperRepository
from app.core.db.episodic_repo import EpisodicRepository


class ChatDatabase:
    """Unified facade for thread-safe JSON flat-file repositories.
    
    Delegates domain-specific tasks to dedicated repositories:
      - chat_repo: conversation threads, messages, active thread tracking
      - profile_repo: user accounts, standalone profile, webhooks
      - paper_repo: paper titles, file hash indexing and deduplication
      - episodic_repo: episodic ReACT reasoning steps, user facts, adaptation runs
      - storage: atomic, thread-safe JSON file I/O
    """

    _lock: threading.RLock = StorageEngine._lock

    def __init__(self, db_file: Optional[str] = None):
        if db_file:
            self.db_file = db_file
            self.conversations_dir = os.path.join(os.path.dirname(db_file), "conversations")
        else:
            self.db_file = os.path.join(settings.HISTORY_DIR, "chat_memory_db.json")
            self.conversations_dir = settings.CONVERSATIONS_DIR

        self.storage = StorageEngine(self.db_file)
        self.paper_repo = PaperRepository(self.storage)
        self.profile_repo = ProfileRepository(self.storage)
        self.episodic_repo = EpisodicRepository(self.storage)
        self.chat_repo = ChatRepository(
            storage=self.storage,
            conversations_dir=self.conversations_dir,
            paper_repo=self.paper_repo
        )

    # --- Low-level storage backward compatibility ---
    def _load_fallback(self) -> dict:
        return self.storage.load_index()

    def _save_fallback(self, data: dict):
        self.storage.save_index(data)

    def initialize_db(self):
        """Initializes database schema keys if missing."""
        data = self.storage.load_index()
        for key in ["users", "projects", "episodic_runs", "paper_hashes", "react_memories"]:
            if key not in data:
                data[key] = {} if key not in ("react_memories",) else []
        if "active_conversation_id" not in data:
            data["active_conversation_id"] = None
        self.storage.save_index(data)
        print("[DB] Local JSON database initialized successfully.")

    # --- Active Conversation State ---
    def get_active_conversation_id(self) -> Optional[str]:
        return self.chat_repo.get_active_conversation_id()

    def set_active_conversation_id(self, conversation_id: Optional[str]):
        self.chat_repo.set_active_conversation_id(conversation_id)

    # --- User Accounts & Profile CRUD ---
    def get_user_by_email(self, email: str) -> Optional[dict]:
        return self.profile_repo.get_user_by_email(email)

    def create_user(self, email: str, password_hash: str, full_name: str = "") -> dict:
        return self.profile_repo.create_user(email, password_hash, full_name)

    def sync_user_registry_webhook(self, email: str, username: str):
        self.profile_repo.sync_user_registry_webhook(email, username)

    def get_standalone_user_profile(self) -> dict:
        return self.profile_repo.get_standalone_user_profile()

    def save_standalone_user_profile(self, profile_dict: dict) -> dict:
        return self.profile_repo.save_standalone_user_profile(profile_dict)

    def update_user_profile(self, user_id: str, profile_dict: dict) -> dict:
        return self.profile_repo.update_user_profile(user_id, profile_dict)

    # --- Conversation Files & Messages CRUD ---
    def _get_conversation_path(self, conversation_id: str) -> str:
        return self.chat_repo._get_conversation_path(conversation_id)

    def _load_conversation_file(self, conversation_id: str) -> dict:
        return self.chat_repo._load_conversation_file(conversation_id)

    def _save_conversation_file(self, conversation_id: str, data: dict):
        self.chat_repo._save_conversation_file(conversation_id, data)

    def get_messages(self, conversation_id: str) -> List[dict]:
        return self.chat_repo.get_messages(conversation_id)

    def get_all_conversations(self) -> List[dict]:
        return self.chat_repo.get_all_conversations()

    def delete_conversation(self, conversation_id: str) -> bool:
        return self.chat_repo.delete_conversation(conversation_id)

    def update_conversation_title(self, conversation_id: str, new_title: str) -> bool:
        return self.chat_repo.update_conversation_title(conversation_id, new_title)

    def save_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        attachment: Optional[dict] = None,
        model_used: Optional[str] = None,
        thought: Optional[str] = None,
        action: Optional[str] = None,
        observation: Optional[str] = None,
        answer: Optional[str] = None
    ) -> dict:
        return self.chat_repo.save_message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            attachment=attachment,
            model_used=model_used,
            thought=thought,
            action=action,
            observation=observation,
            answer=answer
        )

    def create_or_update_conversation_for_paper(self, paper_id: str, title: str, filename: Optional[str] = None) -> str:
        return self.chat_repo.create_or_update_conversation_for_paper(paper_id, title, filename)

    # --- Paper Titles & Deduplication ---
    def get_paper_title_by_id_or_name(self, paper_id: Optional[str] = None, filename: Optional[str] = None) -> Optional[str]:
        return self.paper_repo.get_paper_title_by_id_or_name(paper_id, filename)

    def get_paper_by_hash(self, file_hash: str) -> Optional[dict]:
        return self.paper_repo.get_paper_by_hash(file_hash)

    def save_paper_hash(self, file_hash: str, paper_id: str, filename: str, title: str, conversation_id: Optional[str] = None):
        self.paper_repo.save_paper_hash(file_hash, paper_id, filename, title, conversation_id)

    def delete_paper_hash(self, paper_id: str):
        self.paper_repo.delete_paper_hash(paper_id)

    # --- Episodic Memory & User Facts ---
    def save_episodic_react_step(
        self,
        paper_id: Optional[str],
        query: str,
        thought: Optional[str] = None,
        action: Optional[str] = None,
        observation: Optional[str] = None,
        answer: Optional[str] = None
    ):
        self.episodic_repo.save_episodic_react_step(paper_id, query, thought, action, observation, answer)

    def get_episodic_react_memories(self, paper_id: Optional[str] = None) -> List[dict]:
        return self.episodic_repo.get_episodic_react_memories(paper_id)

    def get_user_facts(self, conversation_id: str = "global") -> List[str]:
        return self.episodic_repo.get_user_facts(conversation_id)

    def save_memory_fact(self, fact_text: str, conversation_id: str = "global"):
        self.episodic_repo.save_memory_fact(fact_text, conversation_id)

    def save_episodic_run(self, paper_id: str, paper_title: str, hyperparameters: dict) -> str:
        return self.episodic_repo.save_episodic_run(paper_id, paper_title, hyperparameters)

    def get_episodic_runs(self) -> List[dict]:
        return self.episodic_repo.get_episodic_runs()
