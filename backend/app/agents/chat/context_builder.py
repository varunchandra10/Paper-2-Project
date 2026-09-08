import os
from typing import Optional, Dict, Any
from app.core.config import settings
from app.core.prompts import build_chat_react_prompt
from app.agents.chat.react_utils import clean_react_content


def resolve_active_paper_id(db: Any, conversation_id: str, paper_id: Optional[str] = None) -> Optional[str]:
    """Auto-resolves the active paper_id from conversation metadata or single extracted JSON."""
    if paper_id:
        return paper_id

    try:
        conv_data = db._load_conversation_file(conversation_id)
        paper_id = conv_data.get("project_id") or conv_data.get("paper_id")
    except Exception:
        pass

    if not paper_id and os.path.exists(settings.EXTRACTED_JSON_DIR):
        try:
            json_files = [f for f in os.listdir(settings.EXTRACTED_JSON_DIR) if f.endswith(".json")]
            if len(json_files) == 1:
                paper_id = json_files[0].replace(".json", "")
        except Exception:
            pass

    return paper_id


def build_context_prompt(
    db: Any,
    tools: Dict[str, Any],
    conversation_id: str,
    query: str,
    paper_id: Optional[str] = None
) -> str:
    """Assembles user facts, extracted hyperparameters, episodic memory, and recent chat history into LLM prompt."""
    paper_id = resolve_active_paper_id(db, conversation_id, paper_id)

    # 1. User facts
    facts = db.get_user_facts(conversation_id) if hasattr(db, "get_user_facts") else []
    facts_text = "\n".join([f"- {f}" for f in facts]) if facts else "No specific user preferences saved."

    # 2. Hyperparameters, Paper RAG Context & Episodic Memory Tools
    approved_params_text = tools["get_hyperparameters"].run(paper_id=paper_id) if paper_id and "get_hyperparameters" in tools else "No paper selected."
    paper_context_text = tools["vector_search"].run(query=query, paper_id=paper_id) if paper_id and "vector_search" in tools else "No active paper context loaded."
    canonical_summary = tools["get_canonical_document"].run(query="summary", paper_id=paper_id) if paper_id and "get_canonical_document" in tools else "No canonical document structure."
    episodic_memory_text = tools["query_episodic_memory"].execute(paper_id=paper_id) if "query_episodic_memory" in tools else "No episodic memory available."

    # 3. Recent history with ReACT reasoning awareness
    all_msgs = db.get_messages(conversation_id) if hasattr(db, "get_messages") else []
    recent_msgs = all_msgs[-6:] if all_msgs else []
    history_items = []
    for m in recent_msgs:
        role = m.get("role", "user").upper()
        if role == "USER":
            history_items.append(f"[USER]: {m.get('content', '')}")
        else:
            ans = m.get("answer") or clean_react_content(m.get("content", ""))
            th = m.get("thought")
            obs = m.get("observation")
            if th:
                th_condensed = th.replace("\n", " ")[:260] + ("..." if len(th) > 260 else "")
                obs_condensed = obs.replace("\n", " ")[:200] + ("..." if len(obs) > 200 else "") if obs else ""
                history_items.append(
                    f"[ASSISTANT (Prior ReACT Thoughts & Deductions)]:\n"
                    f"  - Prior Reasoning: {th_condensed}\n"
                    + (f"  - Verified Discovery: {obs_condensed}\n" if obs_condensed else "")
                    + f"  - Final Answer: {ans[:300]}..."
                )
            else:
                history_items.append(f"[ASSISTANT]: {ans}")

    history_str = "\n\n".join(history_items) if history_items else "No recent messages."

    return build_chat_react_prompt(
        query=query,
        facts_text=facts_text,
        approved_params_text=approved_params_text,
        paper_context_text=paper_context_text,
        canonical_summary=canonical_summary,
        episodic_memory_text=episodic_memory_text,
        history_str=history_str
    )
