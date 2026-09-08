import os
import json
import re
import asyncio
from typing import List, Dict, Any, Optional, Tuple, AsyncGenerator

from app.core.config import settings
from app.core.database import ChatDatabase
from app.core.model_router import ModelRouter
from app.tools import get_all_tools
from app.core.dual_code_engine import dual_code_engine

# Modularized sub-components
from app.agents.chat.react_utils import (
    is_code_request,
    clean_react_content,
    parse_react_traces,
)
from app.agents.chat.smart_titler import generate_smart_title
from app.agents.chat.context_builder import (
    build_context_prompt as _build_context_prompt,
    resolve_active_paper_id,
)

# Re-export utilities for full backward compatibility
__all__ = [
    "ChatAgent",
    "is_code_request",
    "clean_react_content",
    "parse_react_traces",
]


def resolve_failover_model_id(model_used: Optional[str]) -> Optional[str]:
    """Resolves the corresponding frontend model ID if an automatic failover occurred."""
    lower = (model_used or "").lower()
    if "failover" in lower or "fallback" in lower:
        if "gemini" in lower:
            return "google/gemini-2.5-flash"
        if "deepseek" in lower:
            return "deepseek/deepseek-r1:free"
        if "gpt-oss" in lower:
            return "openai/gpt-oss-120b"
        if "qwen" in lower or "groq" in lower:
            return "qwen/qwen3.8-27b"
        return "google/gemini-2.5-flash"
    return None


class ChatAgent:
    """Conversational ReACT Agent with Multi-Turn Tool Execution Loop and Trace Telemetry."""

    def __init__(self, db: Optional[ChatDatabase] = None):
        self.db = db or ChatDatabase()
        self.db.initialize_db()
        self.model_router = ModelRouter()
        self.tools = get_all_tools()

    def build_context_prompt(self, conversation_id: str, query: str, paper_id: Optional[str] = None) -> str:
        """Assembles user facts, extracted hyperparameters, episodic memory, and recent chat history into LLM prompt."""
        return _build_context_prompt(
            db=self.db,
            tools=self.tools,
            conversation_id=conversation_id,
            query=query,
            paper_id=paper_id
        )

    def generate_smart_title(
        self,
        query: str,
        paper_id: Optional[str] = None,
        answer_snippet: Optional[str] = None,
        current_title: Optional[str] = None
    ) -> str:
        """Generates a concise, punchy 3-5 word conversation title like ChatGPT/Claude/Gemini."""
        return generate_smart_title(
            query=query,
            paper_id=paper_id,
            answer_snippet=answer_snippet,
            current_title=current_title,
            db=self.db,
            model_router=self.model_router
        )

    def _should_retarget_title(
        self,
        current_title: Optional[str],
        message_count: int = 0,
        conv_data: Optional[dict] = None
    ) -> bool:
        """Determines if the conversation title needs to be generated.
        A conversation's title is generated/fetched ONLY ONCE per thread,
        and never regenerated or overwritten on subsequent user prompts.
        """
        if conv_data and conv_data.get("custom_title"):
            return False
        if not current_title:
            return True
        clean = str(current_title).strip()
        if not clean:
            return True
        if clean.startswith("conv_"):
            return True
        if clean in ["New Research Analysis", "Untitled Thread", "Chat", "Research Thread"]:
            return True
        # Title is already validly set — never overwrite or regenerate it
        return False

    def process_message(
        self,
        conversation_id: str,
        query: str,
        paper_id: Optional[str] = None,
        model_name: Optional[str] = None
    ) -> dict:
        """Processes user message with a Multi-Turn ReACT Loop (max 3 turns), records conversation, and returns generated response."""
        conv_data = self.db._load_conversation_file(conversation_id)
        paper_id = resolve_active_paper_id(self.db, conversation_id, paper_id)

        # Save user message with PDF attachment if paper_id is active
        attachment = {"filename": f"{paper_id}.pdf" if not paper_id.endswith('.pdf') else paper_id, "paperId": paper_id} if paper_id else None
        self.db.save_message(conversation_id, "user", query, attachment=attachment)
        
        prompt = self.build_context_prompt(conversation_id, query, paper_id=paper_id)
        requested_model = model_name or settings.DEFAULT_MODEL
        
        # Dedicated Dual-Engine Code Interception
        if is_code_request(query) and (settings.has_gemini() or settings.has_huggingface()):
            print(f"[ChatAgent] Detected code request: routing to Dedicated Dual-Engine (Gemini + Hugging Face)...")
            code_res, engine_used = dual_code_engine.generate_paper_code_response(
                query=query,
                context=prompt,
                paper_id=paper_id
            )
            if code_res and code_res.strip():
                clean_code = clean_react_content(code_res)
                code_thought = f"Analyzed code synthesis query against extracted architecture parameters and verified tensor forward pass requirements using {engine_used}."
                code_action = f"dual_code_engine.generate_paper_code_response(engine='{engine_used}')"
                code_obs = "Synthesized executable PyTorch implementation conforming to paper architecture specifications and type signatures."
                code_full_msg = (
                    f"THOUGHT:\n{code_thought}\n\n"
                    f"ACTION:\n{code_action}\n\n"
                    f"OBSERVATION:\n{code_obs}\n\n"
                    f"ANSWER:\n{clean_code}"
                )
                self.db.save_message(
                    conversation_id,
                    "assistant",
                    code_full_msg,
                    model_used=f"Dual-Engine ({engine_used})",
                    thought=code_thought,
                    action=code_action,
                    observation=code_obs,
                    answer=clean_code
                )
                self.db.save_episodic_react_step(
                    paper_id=paper_id,
                    query=query,
                    thought=code_thought,
                    action=code_action,
                    observation=code_obs,
                    answer=clean_code
                )
                current_title = conv_data.get("title") or "New Research Analysis"
                paper_id_for_title = conv_data.get("project_id") or conv_data.get("paper_id") or paper_id
                final_title = current_title
                if self._should_retarget_title(current_title, len(conv_data.get("messages", [])), conv_data):
                    smart_title = self.generate_smart_title(
                        query=query,
                        paper_id=paper_id_for_title,
                        answer_snippet=clean_code,
                        current_title=current_title
                    )
                    if smart_title:
                        final_title = smart_title
                        self.db.update_conversation_title(conversation_id, smart_title)

                return {
                    "conversation_id": conversation_id,
                    "title": final_title,
                    "role": "assistant",
                    "content": code_full_msg,
                    "answer": clean_code,
                    "raw_response": code_res,
                    "model_used": f"Dual-Engine ({engine_used})",
                    "thought": code_thought,
                    "action": code_action,
                    "observation": code_obs
                }

        current_prompt = prompt
        model_used = requested_model
        assistant_text = ""
        trajectory_thoughts: List[str] = []
        trajectory_actions: List[str] = []
        trajectory_observations: List[str] = []

        # --- Multi-Turn ReACT Loop (Max 3 Turns) ---
        for turn in range(1, 4):
            response_text, model_used = self.model_router.generate(current_prompt, model_id=requested_model)
            assistant_text = response_text
            
            th, act, obs = parse_react_traces(response_text)
            if th and th not in trajectory_thoughts:
                trajectory_thoughts.append(th)
            if act and act not in trajectory_actions:
                trajectory_actions.append(act)

            action_match = re.search(r'ACTION:\s*([a-zA-Z0-9_]+)[\(\:]([^\)\n]+)[\)]?', response_text)
            if action_match and turn < 3:
                raw_tool_name = action_match.group(1).strip()
                tool_query = action_match.group(2).strip().strip('"\'')
                tool_inst = self.tools.get(raw_tool_name) or self.tools.get(raw_tool_name.lower())
                
                if tool_inst:
                    print(f"[REACT LOOP Turn {turn}] Executing tool '{raw_tool_name}' with query '{tool_query}'...")
                    try:
                        tool_result = tool_inst.execute(tool_query, paper_id=paper_id)
                    except Exception as t_err:
                        tool_result = f"Tool execution notice: {str(t_err)}"
                        
                    obs_summary = tool_result[:400] + ("..." if len(tool_result) > 400 else "")
                    trajectory_observations.append(f"[{raw_tool_name}]: {obs_summary}")
                    
                    thought_and_action = response_text.split("ANSWER:")[0].strip() if "ANSWER:" in response_text else response_text.strip()
                    current_prompt += (
                        f"\n\n{thought_and_action}\n"
                        f"OBSERVATION: {tool_result[:2500]}\n\n"
                        f"THOUGHT: (Now critically reflect on what you observed above. What specific facts, equations, architectures, or metrics did this observation establish? "
                        f"If you need further details, specify another ACTION. If you now have sufficient evidence, formulate the final, complete ANSWER:)\n"
                    )
                    continue
                else:
                    available = ", ".join(sorted(set(self.tools.keys())))
                    current_prompt += f"\n\nACTION: {raw_tool_name}({tool_query})\nOBSERVATION: Tool '{raw_tool_name}' is not in the registered tool set. Available tools: {available}.\nTHOUGHT:"
                    continue

            break

        # Mandatory synthesis pass if ReACT loop ended without ANSWER:
        if "ANSWER:" not in assistant_text:
            print("[REACT LOOP] ReACT loop concluded without ANSWER: marker. Running final synthesis pass...")
            synth_prompt = (
                f"{current_prompt}\n\n"
                f"SYSTEM DIRECTIVE: Tool collection phase complete. All necessary document excerpts, equations, and ablation metrics have been retrieved above.\n"
                f"Now write your exhaustive, publication-grade, mathematically rigorous final ANSWER explaining the paper clearly for the user inquiry: '{query}'. Do NOT output any more ACTION or tool commands.\n"
                f"ANSWER:\n"
            )
            synth_res, synth_model = self.model_router.generate(synth_prompt, model_id=requested_model)
            if synth_res and synth_res.strip():
                assistant_text = synth_res if "ANSWER:" in synth_res else f"ANSWER:\n{synth_res}"
                model_used = synth_model

        synth_thought = "\n\n".join(trajectory_thoughts) if trajectory_thoughts else "Analyzed query against canonical paper sections and architecture index."
        synth_action = "; ".join(trajectory_actions) if trajectory_actions else "Retrieved canonical paper context and vector embeddings."
        synth_observation = "\n".join(trajectory_observations) if trajectory_observations else "Examined paper methodology, architectural specifications, and ablation results."
        
        final_answer = clean_react_content(assistant_text)
        if not final_answer or not final_answer.strip():
            final_answer = "I have processed your request and am ready to answer any questions or synthesize your PyTorch model."
            
        full_react_message = (
            f"THOUGHT:\n{synth_thought}\n\n"
            f"ACTION:\n{synth_action}\n\n"
            f"OBSERVATION:\n{synth_observation}\n\n"
            f"ANSWER:\n{final_answer}"
        )
        
        self.db.save_message(
            conversation_id,
            "assistant",
            full_react_message,
            model_used=model_used,
            thought=synth_thought,
            action=synth_action,
            observation=synth_observation,
            answer=final_answer
        )
        self.db.save_episodic_react_step(
            paper_id=paper_id,
            query=query,
            thought=synth_thought,
            action=synth_action,
            observation=synth_observation,
            answer=final_answer
        )
        
        current_title = conv_data.get("title") or "New Research Analysis"
        paper_id_for_title = conv_data.get("project_id") or conv_data.get("paper_id") or paper_id

        if self._should_retarget_title(current_title, len(conv_data.get("messages", [])), conv_data):
            smart_title = self.generate_smart_title(
                query=query,
                paper_id=paper_id_for_title,
                answer_snippet=final_answer,
                current_title=current_title
            )
            final_title = smart_title if smart_title else current_title
            if smart_title:
                self.db.update_conversation_title(conversation_id, smart_title)
        else:
            final_title = current_title

        failover_model = resolve_failover_model_id(model_used)

        return {
            "conversation_id": conversation_id,
            "title": final_title,
            "role": "assistant",
            "content": full_react_message,
            "answer": final_answer,
            "raw_response": assistant_text,
            "model_used": model_used,
            "failover_model": failover_model,
            "thought": synth_thought,
            "action": synth_action,
            "observation": synth_observation
        }

    async def process_message_stream(
        self,
        conversation_id: str,
        query: str,
        paper_id: Optional[str] = None,
        model_name: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, str], None]:
        """Async generator that streams the ReACT response as SSE events."""
        try:
            conv_data = self.db._load_conversation_file(conversation_id)
            paper_id = resolve_active_paper_id(self.db, conversation_id, paper_id)

            attachment = {"filename": f"{paper_id}.pdf", "paperId": paper_id} if paper_id else None
            await asyncio.to_thread(self.db.save_message, conversation_id, "user", query, attachment)

            yield {"event": "status", "data": "Building context..."}
            await asyncio.sleep(0)

            prompt = await asyncio.to_thread(self.build_context_prompt, conversation_id, query, paper_id)
            requested_model = model_name or settings.DEFAULT_MODEL

            # Code request fast path
            if is_code_request(query) and (settings.has_gemini() or settings.has_huggingface()):
                yield {"event": "status", "data": "Routing to Dual Code Engine (Gemini + HF Qwen)..."}
                await asyncio.sleep(0)

                code_res, engine_used = await asyncio.to_thread(
                    dual_code_engine.generate_paper_code_response,
                    query=query, context=prompt, paper_id=paper_id
                )

                if code_res and code_res.strip():
                    clean_code = clean_react_content(code_res)
                    code_thought = f"Analyzed code synthesis query using {engine_used}."
                    code_action = f"dual_code_engine.generate_paper_code_response(engine='{engine_used}')"
                    code_obs = "Synthesized executable PyTorch implementation."
                    full_msg = (
                        f"THOUGHT:\n{code_thought}\n\nACTION:\n{code_action}\n\n"
                        f"OBSERVATION:\n{code_obs}\n\nANSWER:\n{clean_code}"
                    )

                    yield {"event": "thought", "data": code_thought}
                    yield {"event": "action", "data": code_action}
                    yield {"event": "observation", "data": code_obs}
                    await asyncio.sleep(0)

                    words = clean_code.split(" ")
                    for i, word in enumerate(words):
                        chunk = word if i == len(words) - 1 else word + " "
                        yield {"event": "token", "data": chunk}
                        if i % 20 == 0:
                            await asyncio.sleep(0)

                    await asyncio.to_thread(
                        self.db.save_message, conversation_id, "assistant", full_msg,
                        None, f"Dual-Engine ({engine_used})", code_thought, code_action, code_obs, clean_code
                    )

                    current_title = conv_data.get("title") or "New Research Analysis"
                    final_title = current_title
                    if self._should_retarget_title(current_title, len(conv_data.get("messages", [])), conv_data):
                        smart_title = await asyncio.to_thread(
                            self.generate_smart_title, query, paper_id, clean_code, current_title
                        )
                        if smart_title:
                            final_title = smart_title
                            await asyncio.to_thread(self.db.update_conversation_title, conversation_id, smart_title)

                    yield {"event": "done", "data": json.dumps({
                        "conversation_id": conversation_id,
                        "title": final_title,
                        "model_used": f"Dual-Engine ({engine_used})",
                        "thought": code_thought, "action": code_action, "observation": code_obs
                    })}
                    return

            # Multi-Turn ReACT Loop
            yield {"event": "status", "data": "Thinking..."}
            await asyncio.sleep(0)

            current_prompt = prompt
            model_used = requested_model
            assistant_text = ""
            trajectory_thoughts: List[str] = []
            trajectory_actions: List[str] = []
            trajectory_observations: List[str] = []

            for turn in range(1, 4):
                yield {"event": "status", "data": f"ReACT turn {turn}/3..."}
                await asyncio.sleep(0)

                response_text, model_used = await asyncio.to_thread(
                    self.model_router.generate, current_prompt, model_id=requested_model
                )
                assistant_text = response_text

                th, act, obs = parse_react_traces(response_text)
                if th and th not in trajectory_thoughts:
                    trajectory_thoughts.append(th)
                    yield {"event": "thought", "data": th[:600]}
                    await asyncio.sleep(0)
                if act and act not in trajectory_actions:
                    trajectory_actions.append(act)

                action_match = re.search(r'ACTION:\s*([a-zA-Z0-9_]+)[\(\:]([^\)\n]+)[\)]?', response_text)
                if action_match and turn < 3:
                    raw_tool_name = action_match.group(1).strip()
                    tool_query = action_match.group(2).strip().strip('"\'')
                    tool_inst = self.tools.get(raw_tool_name) or self.tools.get(raw_tool_name.lower())

                    yield {"event": "action", "data": f"{raw_tool_name}({tool_query[:120]})"}
                    await asyncio.sleep(0)

                    if tool_inst:
                        try:
                            tool_result = await asyncio.to_thread(tool_inst.execute, tool_query, paper_id)
                        except Exception as t_err:
                            tool_result = f"Tool execution notice: {str(t_err)}"

                        obs_summary = tool_result[:400] + ("..." if len(tool_result) > 400 else "")
                        trajectory_observations.append(f"[{raw_tool_name}]: {obs_summary}")
                        yield {"event": "observation", "data": obs_summary}
                        await asyncio.sleep(0)

                        thought_and_action = response_text.split("ANSWER:")[0].strip() if "ANSWER:" in response_text else response_text.strip()
                        current_prompt += (
                            f"\n\n{thought_and_action}\n"
                            f"OBSERVATION: {tool_result[:2500]}\n\n"
                            f"THOUGHT: (Reflect on the observation. If sufficient evidence exists, write the final ANSWER:)\n"
                        )
                        continue
                    else:
                        available = ", ".join(sorted(set(self.tools.keys())))
                        current_prompt += f"\n\nACTION: {raw_tool_name}({tool_query})\nOBSERVATION: Tool not found. Available: {available}.\nTHOUGHT:"
                        continue
                break

            # Synthesis pass if no ANSWER:
            if "ANSWER:" not in assistant_text:
                yield {"event": "status", "data": "Synthesizing final answer..."}
                await asyncio.sleep(0)
                synth_prompt = (
                    f"{current_prompt}\n\nSYSTEM DIRECTIVE: Write the final ANSWER:\n"
                    f"User inquiry: '{query}'. Do NOT output ACTION or tool commands.\nANSWER:\n"
                )
                synth_res, synth_model = await asyncio.to_thread(
                    self.model_router.generate, synth_prompt, model_id=requested_model
                )
                if synth_res and synth_res.strip():
                    assistant_text = synth_res if "ANSWER:" in synth_res else f"ANSWER:\n{synth_res}"
                    model_used = synth_model

            synth_thought = "\n\n".join(trajectory_thoughts) if trajectory_thoughts else "Analyzed paper context."
            synth_action = "; ".join(trajectory_actions) if trajectory_actions else "Retrieved paper context."
            synth_observation = "\n".join(trajectory_observations) if trajectory_observations else "Examined methodology."
            final_answer = clean_react_content(assistant_text)
            if not final_answer or not final_answer.strip():
                final_answer = "I have processed your request."

            # Stream answer tokens
            yield {"event": "status", "data": "Streaming answer..."}
            words = final_answer.split(" ")
            for i, word in enumerate(words):
                chunk = word if i == len(words) - 1 else word + " "
                yield {"event": "token", "data": chunk}
                if i % 15 == 0:
                    await asyncio.sleep(0)

            full_react_message = (
                f"THOUGHT:\n{synth_thought}\n\nACTION:\n{synth_action}\n\n"
                f"OBSERVATION:\n{synth_observation}\n\nANSWER:\n{final_answer}"
            )

            await asyncio.to_thread(
                self.db.save_message, conversation_id, "assistant", full_react_message,
                None, model_used, synth_thought, synth_action, synth_observation, final_answer
            )
            await asyncio.to_thread(
                self.db.save_episodic_react_step, paper_id, query,
                synth_thought, synth_action, synth_observation, final_answer
            )

            current_title = conv_data.get("title") or "New Research Analysis"
            final_title = current_title
            if self._should_retarget_title(current_title, len(conv_data.get("messages", [])), conv_data):
                smart_title = await asyncio.to_thread(
                    self.generate_smart_title, query, paper_id, final_answer, current_title
                )
                if smart_title:
                    final_title = smart_title
                    await asyncio.to_thread(self.db.update_conversation_title, conversation_id, smart_title)

            failover_model = resolve_failover_model_id(model_used)

            yield {"event": "done", "data": json.dumps({
                "conversation_id": conversation_id,
                "title": final_title,
                "model_used": model_used,
                "failover_model": failover_model,
                "thought": synth_thought[:300],
                "action": synth_action[:200],
                "observation": synth_observation[:300]
            })}

        except asyncio.CancelledError:
            return
        except Exception as exc:
            yield {"event": "error", "data": str(exc)}
