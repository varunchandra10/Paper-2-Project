import os
import re
import json
import datetime
from typing import List, Dict, Any, Optional
from app.core.config import settings


class ChatDatabase:
    """JSON database engine managing users, projects, messages, facts, and episodic memory."""

    def __init__(self, db_file: Optional[str] = None):
        if db_file:
            self.db_file = db_file
            self.conversations_dir = os.path.join(os.path.dirname(db_file), "conversations")
        else:
            self.db_file = os.path.join(settings.HISTORY_DIR, "chat_memory_db.json")
            self.conversations_dir = settings.CONVERSATIONS_DIR
        os.makedirs(self.conversations_dir, exist_ok=True)

    def _load_fallback(self) -> dict:
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[DB WARN] Failed to read database JSON file ({e}), initializing empty fallback.")
        return {"users": {}, "projects": {}, "episodic_runs": {}}

    def _save_fallback(self, data: dict):
        try:
            with open(self.db_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[DB ERROR] Failed to save database JSON file: {e}")

    def initialize_db(self):
        """Initializes database schema if keys missing."""
        data = self._load_fallback()
        for key in ["users", "projects", "episodic_runs"]:
            if key not in data:
                data[key] = {}
        self._save_fallback(data)
        print("[DB] Local JSON database initialized successfully.")

    # --- User Accounts CRUD ---
    def get_user_by_email(self, email: str) -> Optional[dict]:
        data = self._load_fallback()
        users = data.get("users", {})
        for uid, u in users.items():
            if u.get("email") == email:
                return u
        return None

    def create_user(self, email: str, password_hash: str, full_name: str = "") -> dict:
        data = self._load_fallback()
        if "users" not in data:
            data["users"] = {}
        user_id = f"usr_{len(data['users']) + 1}"
        user_data = {
            "id": user_id,
            "email": email,
            "password_hash": password_hash,
            "full_name": full_name,
            "created_at": datetime.datetime.now().isoformat()
        }
        data["users"][user_id] = user_data
        self._save_fallback(data)
        return user_data

    def export_users_to_excel(self):
        """Exports all registered users and extended profile details to an Excel spreadsheet."""
        try:
            import xlsxwriter
            excel_path = os.path.join(settings.HISTORY_DIR, "user_profiles.xlsx")
            data = self._load_fallback()
            users = data.get("users", {})
            
            workbook = xlsxwriter.Workbook(excel_path)
            worksheet = workbook.add_worksheet("User Profiles")
            headers = ["User ID", "Username", "Email", "DOB", "Age", "Phone Number", "Project Path", "Ollama Link", "Avatar ID", "Updated At"]
            
            # Format header row
            header_format = workbook.add_format({'bold': True, 'bg_color': '#D4A338', 'font_color': '#FFFFFF'})
            for col_num, header in enumerate(headers):
                worksheet.write(0, col_num, header, header_format)
            
            row_num = 1
            for uid, u in users.items():
                worksheet.write(row_num, 0, str(u.get("id", uid)))
                worksheet.write(row_num, 1, str(u.get("username") or u.get("full_name") or ""))
                worksheet.write(row_num, 2, str(u.get("email") or ""))
                worksheet.write(row_num, 3, str(u.get("dob") or ""))
                worksheet.write(row_num, 4, str(u.get("age") or ""))
                worksheet.write(row_num, 5, str(u.get("phoneNumber") or u.get("phone_number") or ""))
                worksheet.write(row_num, 6, str(u.get("projectPath") or u.get("project_path") or ""))
                worksheet.write(row_num, 7, str(u.get("ollamaLink") or u.get("ollama_link") or ""))
                worksheet.write(row_num, 8, str(u.get("avatarId") or u.get("avatar_id") or "mr-nerdy"))
                worksheet.write(row_num, 9, str(u.get("updated_at") or datetime.datetime.now().isoformat()))
                row_num += 1
            
            workbook.close()
            print(f"[DB EXCEL] Successfully exported {len(users)} user profiles to '{excel_path}'.")
        except Exception as e:
            print(f"[DB WARN] Excel export warning: {e}")

    def update_user_profile(self, user_id: str, profile_dict: dict) -> dict:
        """Updates user profile details in JSON database and syncs to user_profiles.xlsx."""
        data = self._load_fallback()
        if "users" not in data:
            data["users"] = {}
        
        user_data = data["users"].get(user_id) or {}
        user_data["id"] = user_id
        for k, v in profile_dict.items():
            if v is not None:
                user_data[k] = v
        user_data["updated_at"] = datetime.datetime.now().isoformat()
        
        data["users"][user_id] = user_data
        self._save_fallback(data)
        self.export_users_to_excel()
        return user_data

    # --- Individual Conversation JSON CRUD (Indexed by conversation_id) ---
    def _get_conversation_path(self, conversation_id: str) -> str:
        clean_id = re.sub(r'[^a-zA-Z0-9_\-]', '', conversation_id)
        return os.path.join(self.conversations_dir, f"{clean_id}.json")

    def _load_conversation_file(self, conversation_id: str) -> dict:
        filepath = self._get_conversation_path(conversation_id)
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[DB WARN] Failed to read conversation JSON file {filepath}: {e}")
        return {
            "id": conversation_id,
            "title": conversation_id,
            "created_at": datetime.datetime.now().isoformat(),
            "updated_at": datetime.datetime.now().isoformat(),
            "messages": [],
            "user_facts": []
        }

    def _save_conversation_file(self, conversation_id: str, data: dict):
        filepath = self._get_conversation_path(conversation_id)
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[DB ERROR] Failed to save conversation JSON file {filepath}: {e}")

    def get_messages(self, conversation_id: str) -> List[dict]:
        """Loads messages O(1) directly from storage/history/conversations/{conversation_id}.json."""
        conv_data = self._load_conversation_file(conversation_id)
        return conv_data.get("messages", [])

    def get_all_conversations(self) -> List[dict]:
        """Scans storage/history/conversations/ directory for all conversation JSON files with human titles."""
        convs = []
        if os.path.exists(self.conversations_dir):
            for f in os.listdir(self.conversations_dir):
                if f.endswith(".json"):
                    filepath = os.path.join(self.conversations_dir, f)
                    try:
                        with open(filepath, "r", encoding="utf-8") as file:
                            d = json.load(file)
                            msgs = d.get("messages", [])
                            
                            # Derive clean human-readable title if missing or raw UUID
                            raw_title = d.get("title", "")
                            title = raw_title
                            if not title or title.startswith("conv_") or title.startswith("Chat -"):
                                derived = None
                                for m in msgs:
                                    att = m.get("attachment")
                                    if att and att.get("filename"):
                                        derived = att["filename"]
                                        break
                                    if m.get("role") == "user" and m.get("content"):
                                        clean_txt = m["content"].strip().replace("\n", " ")
                                        if clean_txt:
                                            derived = clean_txt[:30] + ("..." if len(clean_txt) > 30 else "")
                                            break
                                title = derived or "New Analysis Thread"
                            
                            last_msg = msgs[-1]["content"] if msgs else ""
                            has_user_msg = any(m.get("role") == "user" for m in msgs)
                            
                            # Return active threads
                            convs.append({
                                "id": d.get("id", os.path.splitext(f)[0]),
                                "conversation_id": d.get("id", os.path.splitext(f)[0]),
                                "title": title,
                                "last_message": last_msg,
                                "created_at": d.get("created_at"),
                                "has_user_msg": has_user_msg
                            })
                    except Exception:
                        pass
        # Sort by created_at descending if present
        convs.sort(key=lambda c: c.get("created_at") or "", reverse=True)
        return convs

    def delete_conversation(self, conversation_id: str) -> bool:
        """Deletes specified conversation thread JSON file from storage/history/conversations/."""
        filepath = os.path.join(self.conversations_dir, f"{conversation_id}.json")
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                return True
            except Exception as e:
                print(f"[DB ERROR] Failed to delete conversation file {filepath}: {e}")
        return False

    def save_message(self, conversation_id: str, role: str, content: str, attachment: Optional[dict] = None) -> dict:
        """Appends message and saves directly into storage/history/conversations/{conversation_id}.json."""
        conv_data = self._load_conversation_file(conversation_id)
        
        # Set human-readable title if generic or starting with conv_
        curr_title = conv_data.get("title", "")
        if role == "user" and (not curr_title or curr_title.startswith("conv_") or curr_title.startswith("Chat -")):
            if attachment and attachment.get("filename"):
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
        if attachment:
            msg["attachment"] = attachment
        conv_data["messages"].append(msg)
        conv_data["updated_at"] = datetime.datetime.now().isoformat()
        self._save_conversation_file(conversation_id, conv_data)
        return msg

    # --- User Memory Facts CRUD ---
    def get_user_facts(self, conversation_id: str = "global") -> List[str]:
        data = self._load_fallback()
        projects = data.get("projects", {})
        if conversation_id in projects:
            return projects[conversation_id].get("user_facts", [])
        return []

    def save_memory_fact(self, fact_text: str, conversation_id: str = "global"):
        data = self._load_fallback()
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
            self._save_fallback(data)

    # --- Episodic Cross-Project Memory CRUD ---
    def save_episodic_run(self, paper_id: str, paper_title: str, hyperparameters: dict) -> str:
        """Saves a past paper adaptation run memory into local DB."""
        data = self._load_fallback()
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
        self._save_fallback(data)
        print(f"[DB] Episodic run memory saved for paper '{paper_id}' ({paper_title})")
        return run_id

    def get_episodic_runs(self) -> List[dict]:
        """Returns all recorded episodic run memories."""
        data = self._load_fallback()
        runs_dict = data.get("episodic_runs", {})
        return list(runs_dict.values())
