from app.tools.base_tool import BaseTool
from app.core.database import ChatDatabase


class EpisodicMemoryTool(BaseTool):
    name = "query_episodic_memory"
    description = "Queries recorded past paper adaptation run memories from database."

    def execute(self, query: str = "") -> str:
        db = ChatDatabase()
        db.initialize_db()
        runs = db.get_episodic_runs()
        
        if not runs:
            return "No past paper adaptation run memories recorded yet."
            
        formatted = []
        for r in runs:
            title = r.get("paper_title", "Unknown Title")
            params = r.get("hyperparameters", {})
            params_str = ", ".join([f"{k}={v}" for k, v in params.items()])
            formatted.append(f"• Paper: '{title}' | Overrides: [{params_str}]")
            
        return "Past Cross-Project Adaptation Memories:\n" + "\n".join(formatted)
