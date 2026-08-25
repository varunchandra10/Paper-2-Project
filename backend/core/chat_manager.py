import json
import re
import ollama
from typing import List, Dict, Any, Optional
from core.database import ChatDatabase
from retrieval.vector_db import PaperVectorDB
from retrieval.embeddings import generate_local_embedding


class ChatManager:
    """Orchestrates Phase 9 Days 36-38: context synthesis, rolling summaries,

    and user preference/memory fact extraction.
    """

    def __init__(self, db: ChatDatabase, model_name: str = "qwen2.5-coder:1.5b"):
        self.db = db
        self.model_name = model_name
        self.vector_db = PaperVectorDB()

    def build_context_prompt(self, conversation_id: str, user_id: str, query: str, paper_id: Optional[str] = None) -> str:
        """Assembles context prompt combining rolling summary, user memory facts,

        relevant RAG chunks, and recent messages history.
        """
        # 1. Fetch Rolling Summary (Day 37)
        summary = self.db.get_summary(conversation_id) or "No previous summary."

        # 2. Fetch User Memory Facts (Day 38)
        facts = self.db.get_memory_facts(user_id)
        facts_text = ""
        if facts:
            facts_list = [f"- [{f['category'].upper()}]: {f['fact']}" for f in facts]
            facts_text = "\n".join(facts_list)
        else:
            facts_text = "No recorded preferences or constraints."

        # 3. Retrieve Paper RAG Context (Day 36)
        rag_text = "No paper context retrieved."
        if paper_id:
            try:
                # Generate query vector
                query_vector = generate_local_embedding(query)
                # Fetch top 10 candidates to filter by paper_id post-search
                candidates = self.vector_db.hybrid_search(query, query_vector, top_k=15)
                paper_chunks = [c for c in candidates if c.get("paper_id") == paper_id]
                
                # Take top 3 matching chunks specifically for the active paper
                top_chunks = paper_chunks[:3]
                if top_chunks:
                    chunks_str = []
                    for idx, chunk in enumerate(top_chunks, 1):
                        chunks_str.append(
                            f"Chunk {idx} (Page {chunk.get('page')}, Section {chunk.get('section')}):\n"
                            f"{chunk.get('content')}"
                        )
                    rag_text = "\n\n".join(chunks_str)
            except Exception as e:
                print(f"[CHAT WARN] Failed to retrieve paper chunks: {e}")

        # 4. Fetch Recent Messages (Last 5 messages to prevent window overflow)
        all_messages = self.db.get_messages(conversation_id)
        recent_messages = all_messages[-5:] if all_messages else []
        
        history_str = ""
        if recent_messages:
            history_str = "\n".join(f"[{m['role'].upper()}]: {m['content']}" for m in recent_messages)
        else:
            history_str = "No recent messages."

        # 5. Compile Prompt Template
        prompt = f"""You are a helpful remote sensing and deep learning engineering assistant.
Answer the user's query utilizing the following context elements.

=========================================
[CONTEXT: USER PREFERENCES & CONSTRAINTS]
{facts_text}

=========================================
[CONTEXT: ROLLING SUMMARY OF OLDER MESSAGES]
{summary}

=========================================
[CONTEXT: RELEVANT PAPER EXTRACTS (RAG)]
{rag_text}

=========================================
[RECENT CHAT HISTORY]
{history_str}

=========================================
User Query: {query}

Provide a concise, technically sound engineering response. Ground your answers in the contexts provided above.
Assistant:"""
        return prompt

    def generate_response(self, conversation_id: str, user_id: str, query: str, paper_id: Optional[str] = None) -> str:
        """Assembles prompt and queries the local Ollama LLM, returning the assistant's reply."""
        prompt = self.build_context_prompt(conversation_id, user_id, query, paper_id)
        try:
            response = ollama.generate(model=self.model_name, prompt=prompt)
            reply = response.get("response", "").strip()
            if not reply:
                reply = "I encountered an empty response from the local model. How else can I assist you?"
            return reply
        except Exception as e:
            return f"Error communicating with local LLM: {str(e)}"

    def extract_and_save_facts(self, user_id: str, message: str):
        """Day 38: Scans user message for persistent facts (preferences/constraints)

        and updates user_memory table. Runs in background.
        """
        prompt = f"""You are a developer profile scanner. Analyze the user's message and extract any persistent developer preferences, machine capabilities, project requirements, or hardware constraints that should be remembered.
Return ONLY a valid JSON list of objects, where each object has:
- "fact": a concise statement of the fact (e.g. "User wants to use PyTorch", "User has an RTX 3060 Laptop GPU").
- "category": either "preference" or "constraint".

If no new persistent facts are mentioned, return an empty JSON list [].
Do not explain or output anything else.

User message: "{message}"
JSON list:"""
        try:
            response = ollama.generate(model=self.model_name, prompt=prompt)
            output = response.get("response", "").strip()
            
            # Clean up potential markdown formatting around JSON
            json_match = re.search(r"\[.*\]", output, re.DOTALL)
            if json_match:
                output = json_match.group(0)
                
            facts = json.loads(output)
            if isinstance(facts, list):
                # Fetch existing facts to prevent duplicate entries
                existing = [f["fact"].lower().strip() for f in self.db.get_memory_facts(user_id)]
                for item in facts:
                    fact = item.get("fact", "").strip()
                    category = item.get("category", "preference").lower().strip()
                    if fact and category in ["preference", "constraint"]:
                        # Deduplicate simple duplicates
                        if fact.lower() not in existing:
                            self.db.add_memory_fact(user_id, fact, category)
                            print(f"[MEMORY] Extracted and saved memory fact: {fact} ({category})")
        except Exception as e:
            print(f"[MEMORY WARN] Failed to parse memory facts: {e}")

    def summarize_conversation_if_needed(self, conversation_id: str):
        """Day 37: Triggers a rolling summary update if active messages exceed 10."""
        messages = self.db.get_messages(conversation_id)
        if len(messages) <= 10:
            return

        # Isolate older messages (all except the last 4)
        older_messages = messages[:-4]
        older_text = "\n".join(f"[{m['role'].upper()}]: {m['content']}" for m in older_messages)
        existing_summary = self.db.get_summary(conversation_id) or "No previous summary."

        prompt = f"""You are a conversation summarizer. Summarize the following chat history between a developer and an assistant, merging it with the existing summary of prior interactions.
Focus strictly on technical decisions, project constraints, and architectural selections. Keep it concise.

Existing Summary: {existing_summary}

Older Messages:
{older_text}

New Summary:"""
        try:
            response = ollama.generate(model=self.model_name, prompt=prompt)
            new_summary = response.get("response", "").strip()
            if new_summary:
                self.db.save_summary(conversation_id, new_summary)
                print(f"[SUMMARY] Conversation summary updated for '{conversation_id}'")
        except Exception as e:
            print(f"[SUMMARY WARN] Failed to generate conversation summary: {e}")
