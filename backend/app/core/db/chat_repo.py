import os
import re
import json
import uuid
import datetime
from typing import Optional, List, Dict, Any
from app.core.config import settings
from app.core.db.storage_engine import StorageEngine
from app.core.db.paper_repo import PaperRepository


class ChatRepository:
    """Repository managing conversation threads, messages, active thread tracking, and titles."""

    def __init__(
        self,
        storage: StorageEngine,
        conversations_dir: Optional[str] = None,
        paper_repo: Optional[PaperRepository] = None
    ):
        self.storage = storage
        self.conversations_dir = conversations_dir or settings.CONVERSATIONS_DIR
        self.paper_repo = paper_repo or PaperRepository(storage)
        os.makedirs(self.conversations_dir, exist_ok=True)

    def _get_conversation_path(self, conversation_id: str) -> str:
        clean_id = re.sub(r'[^a-zA-Z0-9_\-]', '', conversation_id)
        return os.path.join(self.conversations_dir, f"{clean_id}.json")

    def _load_conversation_file(self, conversation_id: str) -> dict:
        filepath = self._get_conversation_path(conversation_id)
        default_conv = {
            "id": conversation_id,
            "title": conversation_id,
            "created_at": datetime.datetime.now().isoformat(),
            "updated_at": datetime.datetime.now().isoformat(),
            "messages": [],
            "user_facts": []
        }
        return self.storage.load_file(filepath, default=default_conv)

    def _save_conversation_file(self, conversation_id: str, data: dict):
        filepath = self._get_conversation_path(conversation_id)
        self.storage.save_file(filepath, data)

    def get_active_conversation_id(self) -> Optional[str]:
        """Returns the ID of the last active conversation if it exists on disk."""
        data = self.storage.load_index()
        active_id = data.get("active_conversation_id")
        if active_id:
            filepath = self._get_conversation_path(active_id)
            if os.path.exists(filepath):
                return active_id
            else:
                self.set_active_conversation_id(None)
        return None

    def set_active_conversation_id(self, conversation_id: Optional[str]):
        """Persists the currently active conversation ID across server restarts."""
        data = self.storage.load_index()
        data["active_conversation_id"] = conversation_id
        self.storage.save_index(data)

    def get_messages(self, conversation_id: str) -> List[dict]:
        """Loads messages O(1) directly from storage/conversations/{conversation_id}.json."""
        conv_data = self._load_conversation_file(conversation_id)
        return conv_data.get("messages", [])

    def get_all_conversations(self) -> List[dict]:
        """Scans storage/conversations/ directory for all conversation JSON files with real paper titles or PDF fallback."""
        convs = []
        if os.path.exists(self.conversations_dir):
            for f in os.listdir(self.conversations_dir):
                if f.endswith(".json"):
                    filepath = os.path.join(self.conversations_dir, f)
                    try:
                        with open(filepath, "r", encoding="utf-8") as file:
                            d = json.load(file)
                            msgs = d.get("messages", [])
                            raw_title = d.get("title", "")

                            cleaned_raw = re.sub(r'^(Ingestion|Analysis|Mock Analysis):\s*', '', raw_title, flags=re.IGNORECASE).strip()
                            is_generic = not cleaned_raw or cleaned_raw.startswith("conv_") or cleaned_raw in ["New Research Analysis", "Untitled Thread", "Research Thread"]
                            is_custom = d.get("custom_title") or (cleaned_raw and not is_generic and not cleaned_raw.lower().endswith(('.pdf', '.docx')))

                            if is_custom:
                                title = cleaned_raw
                            else:
                                paper_id = d.get("project_id") or d.get("paper_id")
                                filename = None
                                for m in msgs:
                                    att = m.get("attachment")
                                    if att:
                                        if not paper_id and att.get("paperId"):
                                            paper_id = att.get("paperId")
                                        if not filename and att.get("filename"):
                                            filename = att.get("filename")

                                if not filename and raw_title:
                                    if cleaned_raw.lower().endswith(('.pdf', '.docx')):
                                        filename = cleaned_raw

                                paper_title = self.paper_repo.get_paper_title_by_id_or_name(paper_id, filename)
                                if paper_title:
                                    title = paper_title
                                else:
                                    fallback_name = filename or cleaned_raw
                                    if not fallback_name or fallback_name.startswith("conv_"):
                                        fallback_name = "New Research Analysis"
                                    title = fallback_name

                            last_msg = msgs[-1]["content"] if msgs else ""
                            has_user_msg = any(m.get("role") == "user" for m in msgs)

                            convs.append({
                                "id": d.get("id", os.path.splitext(f)[0]),
                                "conversation_id": d.get("id", os.path.splitext(f)[0]),
                                "title": title,
                                "project_id": d.get("project_id") or paper_id,
                                "last_message": last_msg,
                                "created_at": d.get("created_at"),
                                "has_user_msg": has_user_msg
                            })
                    except Exception:
                        pass
        convs.sort(key=lambda c: c.get("created_at") or "", reverse=True)
        return convs

    def delete_conversation(self, conversation_id: str) -> bool:
        """Deletes specified conversation thread JSON file."""
        filepath = os.path.join(self.conversations_dir, f"{conversation_id}.json")
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                if self.get_active_conversation_id() == conversation_id:
                    self.set_active_conversation_id(None)
                return True
            except Exception as e:
                print(f"[DB ERROR] Failed to delete conversation file {filepath}: {e}")
        return False

    def update_conversation_title(self, conversation_id: str, new_title: str) -> bool:
        """Updates the human-readable title of a conversation thread."""
        filepath = os.path.join(self.conversations_dir, f"{conversation_id}.json")
        if os.path.exists(filepath):
            try:
                conv_data = self._load_conversation_file(conversation_id)
                conv_data["title"] = new_title.strip()
                conv_data["custom_title"] = True
                conv_data["updated_at"] = datetime.datetime.now().isoformat()
                self._save_conversation_file(conversation_id, conv_data)
                return True
            except Exception as e:
                print(f"[DB ERROR] Failed to update conversation title {filepath}: {e}")
        return False

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
        """Appends message and saves directly into storage/conversations/{conversation_id}.json with ReACT traces."""
        conv_data = self._load_conversation_file(conversation_id)
        
        curr_title = conv_data.get("title", "")
        if attachment and attachment.get("paperId"):
            conv_data["project_id"] = attachment["paperId"]
            conv_data["paper_id"] = attachment["paperId"]
            if not conv_data.get("custom_title") and (not curr_title or curr_title.startswith("conv_") or curr_title == "New Research Analysis"):
                paper_title = self.paper_repo.get_paper_title_by_id_or_name(attachment["paperId"], attachment.get("filename"))
                if paper_title:
                    conv_data["title"] = paper_title

        if role == "user" and (not curr_title or curr_title.startswith("conv_") or curr_title.startswith("Chat -") or curr_title == "New Research Analysis"):
            if conv_data.get("title") and not conv_data["title"].startswith("conv_") and conv_data["title"] != "New Research Analysis":
                pass
            elif attachment and attachment.get("filename"):
                conv_data["title"] = attachment["filename"]
            elif content and content.strip():
                clean_t = content.strip().replace("\n", " ")
                conv_data["title"] = clean_t[:32] + ("..." if len(clean_t) > 32 else "")

        msg = {
            "id": f"msg_{len(conv_data.get('messages', [])) + 1}",
            "role": role,
            "content": content,
            "timestamp": datetime.datetime.now().isoformat()
        }
        if model_used:
            msg["model_used"] = model_used
        if attachment:
            msg["attachment"] = attachment
        if thought:
            msg["thought"] = thought
        if action:
            msg["action"] = action
        if observation:
            msg["observation"] = observation
        if answer:
            msg["answer"] = answer

        if "messages" not in conv_data:
            conv_data["messages"] = []
        conv_data["messages"].append(msg)
        conv_data["updated_at"] = datetime.datetime.now().isoformat()
        self._save_conversation_file(conversation_id, conv_data)
        self.set_active_conversation_id(conversation_id)
        return msg

    def create_or_update_conversation_for_paper(self, paper_id: str, title: str, filename: Optional[str] = None) -> str:
        """Finds or creates a conversation thread specifically associated with a paper and sets its title."""
        clean_title = (title or filename or paper_id).strip()
        if clean_title.startswith("conv_") or clean_title == "Unknown Title":
            clean_title = filename or paper_id

        # 1. Search existing conversations for matching paper_id
        if os.path.exists(self.conversations_dir):
            for f in os.listdir(self.conversations_dir):
                if f.endswith(".json"):
                    cid = os.path.splitext(f)[0]
                    c_data = self._load_conversation_file(cid)
                    c_pid = c_data.get("project_id") or c_data.get("paper_id")
                    if not c_pid:
                        for m in c_data.get("messages", []):
                            if m.get("attachment", {}).get("paperId") == paper_id:
                                c_pid = paper_id
                                break
                    if c_pid == paper_id:
                        c_data["title"] = clean_title
                        c_data["project_id"] = paper_id
                        c_data["paper_id"] = paper_id
                        c_data["updated_at"] = datetime.datetime.now().isoformat()
                        self._save_conversation_file(cid, c_data)
                        self.set_active_conversation_id(cid)
                        return cid

        # 2. Check current active conversation - if empty, repurpose it for this paper!
        active_id = self.get_active_conversation_id()
        if active_id:
            c_data = self._load_conversation_file(active_id)
            if not c_data.get("messages") and not c_data.get("project_id"):
                c_data["title"] = clean_title
                c_data["project_id"] = paper_id
                c_data["paper_id"] = paper_id
                c_data["updated_at"] = datetime.datetime.now().isoformat()
                self._save_conversation_file(active_id, c_data)
                return active_id

        # 3. Create fresh conversation thread
        new_cid = f"conv_{str(uuid.uuid4())[:8]}"
        new_conv = {
            "id": new_cid,
            "conversation_id": new_cid,
            "title": clean_title,
            "project_id": paper_id,
            "paper_id": paper_id,
            "created_at": datetime.datetime.now().isoformat(),
            "updated_at": datetime.datetime.now().isoformat(),
            "messages": []
        }
        self._save_conversation_file(new_cid, new_conv)
        self.set_active_conversation_id(new_cid)
        return new_cid
