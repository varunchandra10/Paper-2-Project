import os
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from app.core.config import settings
from app.core.database import ChatDatabase
from app.core.model_router import ModelRouter
from app.tools import get_all_tools


def clean_react_content(text: str) -> str:
    """Cleans ReACT prefix markers (THOUGHT:, ACTION:, OBSERVATION:, ANSWER:) from content without blanking."""
    if not text or not text.strip():
        return "I am ready to help you analyze your paper and write PyTorch code."
    if "ANSWER:" in text:
        parsed = text.split("ANSWER:")[-1].strip()
        if parsed:
            return parsed
    return text.strip()


def parse_react_traces(text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Extracts THOUGHT, ACTION, and OBSERVATION strings from ReACT prompt output."""
    thought, action, observation = None, None, None
    
    if "THOUGHT:" in text:
        thought_part = text.split("THOUGHT:")[1]
        for stop in ["ACTION:", "OBSERVATION:", "ANSWER:"]:
            thought_part = thought_part.split(stop)[0]
        thought = thought_part.strip()
        
    if "ACTION:" in text:
        action_part = text.split("ACTION:")[1]
        for stop in ["OBSERVATION:", "ANSWER:"]:
            action_part = action_part.split(stop)[0]
        action = action_part.strip()
        
    if "OBSERVATION:" in text:
        obs_part = text.split("OBSERVATION:")[1]
        obs_part = obs_part.split("ANSWER:")[0]
        observation = obs_part.strip()

    return thought, action, observation


class ChatAgent:
    """Conversational ReACT Agent with Multi-Turn Tool Execution Loop and Trace Telemetry."""

    def __init__(self, db: Optional[ChatDatabase] = None):
        self.db = db or ChatDatabase()
        self.db.initialize_db()
        self.model_router = ModelRouter()
        self.tools = get_all_tools()

    def build_context_prompt(self, conversation_id: str, query: str, paper_id: Optional[str] = None) -> str:
        """Assembles user facts, extracted hyperparameters, episodic memory, and recent chat history into LLM prompt."""
        # 1. User facts
        facts = self.db.get_user_facts(conversation_id)
        facts_text = "\n".join([f"- {f}" for f in facts]) if facts else "No specific user preferences saved."

        # 2. Hyperparameters, Paper RAG Context & Episodic Memory Tools
        approved_params_text = self.tools["get_hyperparameters"].run(paper_id=paper_id) if paper_id else "No paper selected."
        paper_context_text = self.tools["vector_search"].run(query=query, paper_id=paper_id) if paper_id else "No active paper context loaded."
        canonical_summary = self.tools["get_canonical_document"].run(paper_id=paper_id, query_type="summary") if paper_id else "No canonical document structure."
        episodic_memory_text = self.tools["query_episodic_memory"].run()

        # 3. Recent history
        all_msgs = self.db.get_messages(conversation_id)
        recent_msgs = all_msgs[-5:] if all_msgs else []
        history_str = "\n".join([f"[{m['role'].upper()}]: {clean_react_content(m['content'])}" for m in recent_msgs]) if recent_msgs else "No recent messages."

        return f"""You are a helpful research assistant and deep learning engineering expert operating under a ReACT framework (Reasoning + Action).

THOUGHT: [Explain your step-by-step reasoning.]
ACTION: [Optional: Specify a tool to execute e.g. search_arxiv("query") or query_knowledge_graph("module")]
OBSERVATION: [Results retrieved from tool or paper context.]
ANSWER: [Your final concise, technically sound, and user-friendly response.]

AVAILABLE TOOLS:
- search_arxiv("query"): Search official ArXiv papers & preprints.
- search_scholar("query"): Query Semantic Scholar literature citations & TL;DR abstracts.
- query_knowledge_graph("module"): Query NetworkX graph for PyTorch layer topology & tensor shapes.
- search_paper_chunks("query"): Search extracted paper text chunks.

RESPONSE FORMATTING RULES:
1. CONVERSATIONAL & EXPLANATORY QUERIES:
   - When asked for summaries, abstracts, explanations, conclusions, references, comparisons, or general questions, respond in CLEAR, BEAUTIFULLY FORMATTED MARKDOWN PROSE.
   - Do NOT wrap general text answers or text variables inside Python code blocks.
2. CODE IMPLEMENTATION QUERIES:
   - ONLY when the user specifically asks for code, scripts, model architectures, or PyTorch implementations: write complete, bug-free Python code enclosed in standard markdown code blocks (```python ... ```).
   - Inject actual hyperparameter values from [CONTEXT: APPROVED HYPERPARAMETERS FOR IMPLEMENTATION].

=========================================
[CONTEXT: USER PREFERENCES & CONSTRAINTS]
{facts_text}

=========================================
[CONTEXT: CANONICAL DOCUMENT STRUCTURE SUMMARY]
{canonical_summary}

=========================================
[CONTEXT: EXTRACTED RESEARCH PAPER TEXT & RAG CHUNKS]
{paper_context_text}

=========================================
[CONTEXT: APPROVED HYPERPARAMETERS FOR IMPLEMENTATION]
{approved_params_text}

=========================================
[CONTEXT: PAST EPISODIC MEMORY (CROSS-PROJECT LESSONS)]
{episodic_memory_text}

=========================================
[RECENT CHAT HISTORY]
{history_str}

USER QUERY: {query}"""

    def process_message(self, conversation_id: str, query: str, paper_id: Optional[str] = None, model_name: Optional[str] = None) -> dict:
        """Processes user message with a Multi-Turn ReACT Loop (max 3 turns), records conversation, and returns generated response."""
        # Save user message with PDF attachment if paper_id is active
        attachment = {"filename": f"{paper_id}.pdf" if not paper_id.endswith('.pdf') else paper_id, "paperId": paper_id} if paper_id else None
        self.db.save_message(conversation_id, "user", query, attachment=attachment)
        
        prompt = self.build_context_prompt(conversation_id, query, paper_id=paper_id)
        requested_model = model_name or settings.DEFAULT_MODEL
        
        current_prompt = prompt
        model_used = requested_model
        assistant_text = ""
        
        last_thought = None
        last_action = None
        last_observation = None

        # --- Multi-Turn ReACT Loop (Max 3 Turns) ---
        for turn in range(1, 4):
            response_text, model_used = self.model_router.generate(current_prompt, model_id=requested_model)
            assistant_text = response_text
            
            # Extract ReACT reasoning trace steps
            th, act, obs = parse_react_traces(response_text)
            if th: last_thought = th
            if act: last_action = act
            if obs: last_observation = obs

            # Check if model requested a tool execution via ACTION: <tool_name>(<query>)
            action_match = re.search(r'ACTION:\s*([a_zA-Z0-9_]+)[\(\:]([^\)\n]+)[\)]?', response_text)
            if action_match and turn < 3:
                tool_name = action_match.group(1).strip()
                tool_query = action_match.group(2).strip().strip('"\'')
                
                if tool_name in self.tools:
                    print(f"[REACT LOOP Turn {turn}] Executing tool '{tool_name}' with query '{tool_query}'...")
                    try:
                        tool_inst = self.tools[tool_name]
                        if hasattr(tool_inst, "execute") and "paper_id" in tool_inst.execute.__code__.co_varnames:
                            tool_result = tool_inst.execute(tool_query, paper_id=paper_id)
                        else:
                            tool_result = tool_inst.run(tool_query)
                    except Exception as t_err:
                        tool_result = f"Tool execution notice: {str(t_err)}"
                        
                    last_observation = tool_result[:300]
                    # Append OBSERVATION to prompt for next turn
                    current_prompt += f"\n\nTHOUGHT: I executed tool '{tool_name}'.\nOBSERVATION: {tool_result}\nNow formulate the final ANSWER:"
                    continue

            # If no action or ANSWER: is reached, complete loop
            break

        # Save assistant message
        self.db.save_message(conversation_id, "assistant", assistant_text)
        
        final_content = assistant_text if assistant_text and assistant_text.strip() else "I have processed your request and am ready to answer any questions or synthesize your PyTorch model."
        
        return {
            "conversation_id": conversation_id,
            "role": "assistant",
            "content": final_content,
            "raw_response": assistant_text,
            "model_used": model_used,
            "thought": last_thought,
            "action": last_action,
            "observation": last_observation
        }
