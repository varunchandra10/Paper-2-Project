import os
import json
import uuid
import datetime
import psycopg2
from typing import List, Dict, Any, Optional
from core.security import hash_password, verify_password

# Load database settings from environment
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv(os.path.join(backend_dir, ".env"))

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")


class ChatDatabase:
    """Manages system users, conversations, messages, summaries, and user memory state.

    Falls back automatically to local JSON flat-file storage if PostgreSQL is unreachable.
    """
    
    def __init__(self, db_url: str = DATABASE_URL):
        self.db_url = db_url
        self.fallback_file = os.path.join(backend_dir, "papers", "chat_memory_db.json")
        self.use_fallback = False
        
        try:
            # Check connection with a short timeout
            conn = psycopg2.connect(self.db_url, connect_timeout=3)
            conn.close()
        except Exception:
            self.use_fallback = True
            print(f"[DB WARN] PostgreSQL database unreachable. Falling back to local JSON storage: {self.fallback_file}")

    def _get_connection(self):
        """Establishes a new PostgreSQL connection."""
        if self.use_fallback:
            raise RuntimeError("Database connection requested, but in local JSON fallback mode.")
        return psycopg2.connect(self.db_url)

    def _load_fallback(self) -> dict:
        """Loads fallback JSON data from disk."""
        if os.path.exists(self.fallback_file):
            try:
                with open(self.fallback_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "users": {},
            "projects": {},
            "conversations": {},
            "messages": {},
            "conversation_summaries": {},
            "user_memory": {}
        }

    def _save_fallback(self, data: dict):
        """Saves fallback JSON data to disk."""
        try:
            with open(self.fallback_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[DB ERROR] Failed to save local fallback DB: {e}")

    def initialize_db(self):
        """Initializes database tables or structures in JSON fallback file."""
        if self.use_fallback:
            data = self._load_fallback()
            # Ensure all keys exist
            for key in ["users", "projects", "conversations", "messages", "conversation_summaries", "user_memory"]:
                if key not in data:
                    data[key] = {}
            self._save_fallback(data)
            print("[DB] Local JSON chat database initialized successfully.")
            return

        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                # 1. Users Table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id TEXT PRIMARY KEY,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        created_at TIMESTAMP NOT NULL DEFAULT NOW()
                    );
                """)
                # 2. Projects Table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS projects (
                        project_id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT,
                        created_at TIMESTAMP NOT NULL DEFAULT NOW()
                    );
                """)
                # 3. Conversations Table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS conversations (
                        conversation_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                        project_id TEXT REFERENCES projects(project_id) ON DELETE SET NULL,
                        title TEXT NOT NULL,
                        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                        updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                    );
                """)
                # 4. Messages Table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS messages (
                        message_id TEXT PRIMARY KEY,
                        conversation_id TEXT NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,
                        role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                        content TEXT NOT NULL,
                        created_at TIMESTAMP NOT NULL DEFAULT NOW()
                    );
                """)
                # 5. Summaries Table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS conversation_summaries (
                        summary_id TEXT PRIMARY KEY,
                        conversation_id TEXT NOT NULL UNIQUE REFERENCES conversations(conversation_id) ON DELETE CASCADE,
                        summary_text TEXT NOT NULL,
                        updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                    );
                """)
                # 6. User Memory Table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS user_memory (
                        memory_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
                        fact TEXT NOT NULL,
                        category TEXT NOT NULL,
                        created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                        updated_at TIMESTAMP NOT NULL DEFAULT NOW()
                    );
                """)
            conn.commit()
            print("[DB] PostgreSQL chat tables initialized successfully.")
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    # --- CRUD operations: USER ---
    
    def add_user(self, username: str, password_hash_or_raw: str, is_hashed: bool = False) -> str:
        """Registers a new user inside the database, returning the user_id."""
        user_id = str(uuid.uuid4())
        pwd_hash = password_hash_or_raw if is_hashed else hash_password(password_hash_or_raw)
        now_str = datetime.datetime.now().isoformat()
        
        if self.use_fallback:
            data = self._load_fallback()
            # Check unique constraint
            for uid, info in data["users"].items():
                if info["username"] == username:
                    raise ValueError(f"User with username '{username}' already exists.")
            data["users"][user_id] = {
                "username": username,
                "password_hash": pwd_hash,
                "created_at": now_str
            }
            self._save_fallback(data)
            return user_id

        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO users (user_id, username, password_hash) VALUES (%s, %s, %s);",
                    (user_id, username, pwd_hash)
                )
            conn.commit()
            return user_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def verify_user(self, username: str, password_raw: str) -> Optional[str]:
        """Verifies raw password against stored hash, returning user_id if valid."""
        if self.use_fallback:
            data = self._load_fallback()
            for uid, info in data["users"].items():
                if info["username"] == username:
                    if verify_password(info["password_hash"], password_raw):
                        return uid
            return None

        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT user_id, password_hash FROM users WHERE username = %s;", (username,))
                row = cur.fetchone()
                if row:
                    user_id, pwd_hash = row
                    if verify_password(pwd_hash, password_raw):
                        return user_id
            return None
        finally:
            conn.close()

    # --- CRUD operations: PROJECTS ---

    def create_project(self, name: str, description: str = "") -> str:
        """Creates a project container, returning project_id."""
        project_id = str(uuid.uuid4())
        now_str = datetime.datetime.now().isoformat()
        
        if self.use_fallback:
            data = self._load_fallback()
            data["projects"][project_id] = {
                "name": name,
                "description": description,
                "created_at": now_str
            }
            self._save_fallback(data)
            return project_id

        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO projects (project_id, name, description) VALUES (%s, %s, %s);",
                    (project_id, name, description)
                )
            conn.commit()
            return project_id
        finally:
            conn.close()

    # --- CRUD operations: CONVERSATIONS ---

    def create_conversation(self, user_id: str, title: str, project_id: Optional[str] = None) -> str:
        """Creates a conversation container, returning conversation_id."""
        conv_id = str(uuid.uuid4())
        now_str = datetime.datetime.now().isoformat()
        
        if self.use_fallback:
            data = self._load_fallback()
            # Foreign key check
            if user_id not in data["users"]:
                raise ValueError(f"User ID {user_id} not found.")
            if project_id and project_id not in data["projects"]:
                raise ValueError(f"Project ID {project_id} not found.")
                
            data["conversations"][conv_id] = {
                "user_id": user_id,
                "project_id": project_id,
                "title": title,
                "created_at": now_str,
                "updated_at": now_str
            }
            self._save_fallback(data)
            return conv_id

        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO conversations (conversation_id, user_id, project_id, title) VALUES (%s, %s, %s, %s);",
                    (conv_id, user_id, project_id, title)
                )
            conn.commit()
            return conv_id
        finally:
            conn.close()

    def list_conversations(self, user_id: str) -> List[dict]:
        """Lists all active conversations for a specific user."""
        if self.use_fallback:
            data = self._load_fallback()
            results = []
            for cid, info in data["conversations"].items():
                if info["user_id"] == user_id:
                    results.append({
                        "conversation_id": cid,
                        "user_id": info["user_id"],
                        "project_id": info["project_id"],
                        "title": info["title"],
                        "created_at": info["created_at"],
                        "updated_at": info["updated_at"]
                    })
            return sorted(results, key=lambda x: x["updated_at"], reverse=True)

        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT conversation_id, user_id, project_id, title, created_at, updated_at "
                    "FROM conversations WHERE user_id = %s ORDER BY updated_at DESC;",
                    (user_id,)
                )
                rows = cur.fetchall()
                return [
                    {
                        "conversation_id": r[0],
                        "user_id": r[1],
                        "project_id": r[2],
                        "title": r[3],
                        "created_at": r[4].isoformat(),
                        "updated_at": r[5].isoformat()
                    }
                    for r in rows
                ]
        finally:
            conn.close()

    def get_conversation(self, conversation_id: str) -> Optional[dict]:
        """Retrieves metadata details for a specific conversation."""
        if self.use_fallback:
            data = self._load_fallback()
            if conversation_id not in data["conversations"]:
                return None
            info = data["conversations"][conversation_id]
            return {
                "conversation_id": conversation_id,
                "user_id": info["user_id"],
                "project_id": info["project_id"],
                "title": info["title"],
                "created_at": info["created_at"],
                "updated_at": info["updated_at"]
            }

        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT conversation_id, user_id, project_id, title, created_at, updated_at "
                    "FROM conversations WHERE conversation_id = %s;",
                    (conversation_id,)
                )
                row = cur.fetchone()
                if row:
                    return {
                        "conversation_id": row[0],
                        "user_id": row[1],
                        "project_id": row[2],
                        "title": row[3],
                        "created_at": row[4].isoformat(),
                        "updated_at": row[5].isoformat()
                    }
                return None
        finally:
            conn.close()


    def rename_conversation(self, conversation_id: str, new_title: str):
        """Renames a conversation's display title."""
        now_str = datetime.datetime.now().isoformat()
        
        if self.use_fallback:
            data = self._load_fallback()
            if conversation_id not in data["conversations"]:
                raise ValueError("Conversation ID not found.")
            data["conversations"][conversation_id]["title"] = new_title
            data["conversations"][conversation_id]["updated_at"] = now_str
            self._save_fallback(data)
            return

        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE conversations SET title = %s, updated_at = NOW() WHERE conversation_id = %s;",
                    (new_title, conversation_id)
                )
            conn.commit()
        finally:
            conn.close()

    def delete_conversation(self, conversation_id: str):
        """Deletes a conversation and all its cascaded messages/summaries."""
        if self.use_fallback:
            data = self._load_fallback()
            if conversation_id in data["conversations"]:
                data["conversations"].pop(conversation_id)
            # Cascade delete messages
            m_to_remove = [mid for mid, info in data["messages"].items() if info["conversation_id"] == conversation_id]
            for mid in m_to_remove:
                data["messages"].pop(mid)
            # Cascade delete summaries
            s_to_remove = [sid for sid, info in data["conversation_summaries"].items() if info["conversation_id"] == conversation_id]
            for sid in s_to_remove:
                data["conversation_summaries"].pop(sid)
            self._save_fallback(data)
            return

        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM conversations WHERE conversation_id = %s;", (conversation_id,))
            conn.commit()
        finally:
            conn.close()

    # --- CRUD operations: MESSAGES ---

    def save_message(self, conversation_id: str, role: str, content: str) -> str:
        """Saves a message in the thread, updating conversation timestamp."""
        msg_id = str(uuid.uuid4())
        now_str = datetime.datetime.now().isoformat()
        
        if self.use_fallback:
            data = self._load_fallback()
            if conversation_id not in data["conversations"]:
                raise ValueError("Conversation ID not found.")
            data["messages"][msg_id] = {
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
                "created_at": now_str
            }
            # Touch updated_at
            data["conversations"][conversation_id]["updated_at"] = now_str
            self._save_fallback(data)
            return msg_id

        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO messages (message_id, conversation_id, role, content) VALUES (%s, %s, %s, %s);",
                    (msg_id, conversation_id, role, content)
                )
                cur.execute(
                    "UPDATE conversations SET updated_at = NOW() WHERE conversation_id = %s;",
                    (conversation_id,)
                )
            conn.commit()
            return msg_id
        finally:
            conn.close()

    def get_messages(self, conversation_id: str) -> List[dict]:
        """Loads complete chronological message list for a conversation."""
        if self.use_fallback:
            data = self._load_fallback()
            results = []
            for mid, info in data["messages"].items():
                if info["conversation_id"] == conversation_id:
                    results.append({
                        "message_id": mid,
                        "conversation_id": info["conversation_id"],
                        "role": info["role"],
                        "content": info["content"],
                        "created_at": info["created_at"]
                    })
            return sorted(results, key=lambda x: x["created_at"])

        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT message_id, conversation_id, role, content, created_at "
                    "FROM messages WHERE conversation_id = %s ORDER BY created_at ASC;",
                    (conversation_id,)
                )
                rows = cur.fetchall()
                return [
                    {
                        "message_id": r[0],
                        "conversation_id": r[1],
                        "role": r[2],
                        "content": r[3],
                        "created_at": r[4].isoformat()
                    }
                    for r in rows
                ]
        finally:
            conn.close()

    # --- CRUD operations: CONVERSATION SUMMARIES ---

    def save_summary(self, conversation_id: str, summary_text: str):
        """Saves or updates the rolling summary block for a conversation."""
        now_str = datetime.datetime.now().isoformat()
        
        if self.use_fallback:
            data = self._load_fallback()
            if conversation_id not in data["conversations"]:
                raise ValueError("Conversation ID not found.")
                
            # Check if summary already exists
            existing_id = None
            for sid, info in data["conversation_summaries"].items():
                if info["conversation_id"] == conversation_id:
                    existing_id = sid
                    break
                    
            if existing_id:
                data["conversation_summaries"][existing_id]["summary_text"] = summary_text
                data["conversation_summaries"][existing_id]["updated_at"] = now_str
            else:
                new_id = str(uuid.uuid4())
                data["conversation_summaries"][new_id] = {
                    "conversation_id": conversation_id,
                    "summary_text": summary_text,
                    "updated_at": now_str
                }
            self._save_fallback(data)
            return

        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO conversation_summaries (summary_id, conversation_id, summary_text, updated_at) "
                    "VALUES (%s, %s, %s, NOW()) "
                    "ON CONFLICT (conversation_id) "
                    "DO UPDATE SET summary_text = EXCLUDED.summary_text, updated_at = NOW();",
                    (str(uuid.uuid4()), conversation_id, summary_text)
                )
            conn.commit()
        finally:
            conn.close()

    def get_summary(self, conversation_id: str) -> Optional[str]:
        """Loads current summary for a conversation, returning None if empty."""
        if self.use_fallback:
            data = self._load_fallback()
            for sid, info in data["conversation_summaries"].items():
                if info["conversation_id"] == conversation_id:
                    return info["summary_text"]
            return None

        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT summary_text FROM conversation_summaries WHERE conversation_id = %s;",
                    (conversation_id,)
                )
                row = cur.fetchone()
                return row[0] if row else None
        finally:
            conn.close()

    # --- CRUD operations: USER MEMORY ---

    def add_memory_fact(self, user_id: str, fact: str, category: str) -> str:
        """Stores a persistent fact extracted about a user."""
        memory_id = str(uuid.uuid4())
        now_str = datetime.datetime.now().isoformat()
        
        if self.use_fallback:
            data = self._load_fallback()
            if user_id not in data["users"]:
                raise ValueError("User ID not found.")
            data["user_memory"][memory_id] = {
                "user_id": user_id,
                "fact": fact,
                "category": category,
                "created_at": now_str,
                "updated_at": now_str
            }
            self._save_fallback(data)
            return memory_id

        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO user_memory (memory_id, user_id, fact, category) VALUES (%s, %s, %s, %s);",
                    (memory_id, user_id, fact, category)
                )
            conn.commit()
            return memory_id
        finally:
            conn.close()

    def get_memory_facts(self, user_id: str) -> List[dict]:
        """Loads all persistent memory facts registered for a user."""
        if self.use_fallback:
            data = self._load_fallback()
            results = []
            for mid, info in data["user_memory"].items():
                if info["user_id"] == user_id:
                    results.append({
                        "memory_id": mid,
                        "user_id": info["user_id"],
                        "fact": info["fact"],
                        "category": info["category"],
                        "created_at": info["created_at"],
                        "updated_at": info["updated_at"]
                    })
            return sorted(results, key=lambda x: x["created_at"])

        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT memory_id, user_id, fact, category, created_at, updated_at "
                    "FROM user_memory WHERE user_id = %s ORDER BY created_at ASC;",
                    (user_id,)
                )
                rows = cur.fetchall()
                return [
                    {
                        "memory_id": r[0],
                        "user_id": r[1],
                        "fact": r[2],
                        "category": r[3],
                        "created_at": r[4].isoformat(),
                        "updated_at": r[5].isoformat()
                    }
                    for r in rows
                ]
        finally:
            conn.close()

    def delete_memory_fact(self, memory_id: str):
        """Deletes a specific user memory fact."""
        if self.use_fallback:
            data = self._load_fallback()
            if memory_id in data["user_memory"]:
                data["user_memory"].pop(memory_id)
            self._save_fallback(data)
            return

        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM user_memory WHERE memory_id = %s;", (memory_id,))
            conn.commit()
        finally:
            conn.close()
