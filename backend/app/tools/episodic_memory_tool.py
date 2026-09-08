from typing import Optional
from app.tools.base_tool import BaseTool
from app.core.database import ChatDatabase


class EpisodicMemoryTool(BaseTool):
    name = "query_episodic_memory"
    description = "Queries recorded past paper adaptation run memories and past ReACT reasoning deductions from database."

    def execute(self, query: str = "", paper_id: Optional[str] = None, *args, **kwargs) -> str:
        db = ChatDatabase()
        db.initialize_db()
        runs = db.get_episodic_runs()
        react_mems = db.get_episodic_react_memories(paper_id=paper_id)
        
        sections = []
        if react_mems:
            r_lines = []
            for m in react_mems[-4:]:
                r_lines.append(
                    f"• User Inquiry: '{m.get('query')}'\n"
                    f"  - Verified Discovery/Evidence: {m.get('observation_summary')}\n"
                    f"  - Key Deductions: {m.get('thought_summary')[:200]}..."
                )
            sections.append("Verified Prior Paper Discoveries & ReACT Traces:\n" + "\n".join(r_lines))

        if runs:
            formatted = []
            for r in runs:
                title = r.get("paper_title", "Unknown Title")
                params = r.get("hyperparameters", {})
                params_str = ", ".join([f"{k}={v}" for k, v in params.items()])
                formatted.append(f"• Paper: '{title}' | Overrides: [{params_str}]")
            sections.append("Past Cross-Project Adaptation Memories:\n" + "\n".join(formatted))
            
        return "\n\n".join(sections) if sections else "No past paper adaptation run memories or prior reasoning recorded yet."
