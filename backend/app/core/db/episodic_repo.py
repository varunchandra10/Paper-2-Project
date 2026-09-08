import datetime
from typing import Optional, List, Dict, Any
from app.core.db.storage_engine import StorageEngine


class EpisodicRepository:
    """Repository managing episodic ReACT steps, cross-project runs, and user memory facts."""

    def __init__(self, storage: StorageEngine):
        self.storage = storage

    def save_episodic_react_step(
        self,
        paper_id: Optional[str],
        query: str,
        thought: Optional[str] = None,
        action: Optional[str] = None,
        observation: Optional[str] = None,
        answer: Optional[str] = None
    ):
        """Persists high-value ReACT reasoning traces to episodic memory so future inference rounds reuse verified deductions."""
        if not paper_id:
            return
        data = self.storage.load_index()
        if "react_memories" not in data:
            data["react_memories"] = []
            
        entry = {
            "paper_id": paper_id,
            "query": query[:200],
            "thought_summary": (thought[:500] + "...") if thought and len(thought) > 500 else (thought or ""),
            "action_executed": action or "",
            "observation_summary": (observation[:400] + "...") if observation and len(observation) > 400 else (observation or ""),
            "answer_summary": (answer[:300] + "...") if answer and len(answer) > 300 else (answer or ""),
            "timestamp": datetime.datetime.now().isoformat()
        }
        data["react_memories"].append(entry)
        if len(data["react_memories"]) > 25:
            data["react_memories"] = data["react_memories"][-25:]
        self.storage.save_index(data)
        print(f"[DB] Persisted ReACT reasoning trace to episodic memory for paper '{paper_id}'.")

    def get_episodic_react_memories(self, paper_id: Optional[str] = None) -> List[dict]:
        """Retrieves past ReACT reasoning traces for a specific paper or globally."""
        data = self.storage.load_index()
        all_mems = data.get("react_memories", [])
        if not paper_id:
            return all_mems
        return [m for m in all_mems if m.get("paper_id") == paper_id]

    def get_user_facts(self, conversation_id: str = "global") -> List[str]:
        """Fetches remembered user preferences and facts."""
        data = self.storage.load_index()
        projects = data.get("projects", {})
        if conversation_id in projects:
            return projects[conversation_id].get("user_facts", [])
        return []

    def save_memory_fact(self, fact_text: str, conversation_id: str = "global"):
        """Saves a learned user preference or fact."""
        data = self.storage.load_index()
        if "projects" not in data:
            data["projects"] = {}
        if conversation_id not in data["projects"]:
            data["projects"][conversation_id] = {
                "id": conversation_id,
                "created_at": datetime.datetime.now().isoformat(),
                "messages": [],
                "user_facts": []
            }
        if fact_text not in data["projects"][conversation_id]["user_facts"]:
            data["projects"][conversation_id]["user_facts"].append(fact_text)
            self.storage.save_index(data)

    def save_episodic_run(self, paper_id: str, paper_title: str, hyperparameters: dict) -> str:
        """Saves a past paper adaptation run memory into local DB."""
        data = self.storage.load_index()
        if "episodic_runs" not in data:
            data["episodic_runs"] = {}
            
        run_id = f"run_{paper_id}"
        data["episodic_runs"][run_id] = {
            "run_id": run_id,
            "paper_id": paper_id,
            "paper_title": paper_title,
            "hyperparameters": hyperparameters,
            "updated_at": datetime.datetime.now().isoformat()
        }
        self.storage.save_index(data)
        print(f"[DB] Episodic run memory saved for paper '{paper_id}' ({paper_title})")
        return run_id

    def get_episodic_runs(self) -> List[dict]:
        """Returns all recorded episodic run memories."""
        data = self.storage.load_index()
        runs_dict = data.get("episodic_runs", {})
        return list(runs_dict.values())
