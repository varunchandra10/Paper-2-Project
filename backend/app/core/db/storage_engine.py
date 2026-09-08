import os
import json
import tempfile
import threading
from typing import Any, Dict, Optional
from app.core.config import settings


class StorageEngine:
    """Thread-safe JSON flat-file atomic read and write engine.
    
    Uses an RLock to serialize operations and an atomic tempfile + os.replace
    pattern so that unexpected process shutdowns or server restarts cannot
    corrupt JSON databases.
    """

    _lock: threading.RLock = threading.RLock()

    def __init__(self, db_file: Optional[str] = None):
        self.db_file = db_file or os.path.join(settings.HISTORY_DIR, "chat_memory_db.json")
        os.makedirs(os.path.dirname(self.db_file), exist_ok=True)

    def load_index(self) -> Dict[str, Any]:
        """Thread-safe read of the global index JSON file."""
        with StorageEngine._lock:
            if os.path.exists(self.db_file):
                try:
                    with open(self.db_file, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception as e:
                    print(f"[DB WARN] Failed to read database JSON file ({e}), initializing fallback.")
            return {"users": {}, "projects": {}, "episodic_runs": {}, "paper_hashes": {}, "react_memories": []}

    def save_index(self, data: Dict[str, Any]):
        """Thread-safe atomic write to the global index JSON file."""
        with StorageEngine._lock:
            dir_name = os.path.dirname(self.db_file)
            os.makedirs(dir_name, exist_ok=True)
            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w", encoding="utf-8",
                    dir=dir_name, delete=False, suffix=".tmp"
                ) as tmp:
                    json.dump(data, tmp, indent=2, ensure_ascii=False)
                    tmp_path = tmp.name
                os.replace(tmp_path, self.db_file)
            except Exception as e:
                print(f"[DB ERROR] Failed to save database JSON file: {e}")
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        pass

    def load_file(self, filepath: str, default: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Thread-safe read of an arbitrary JSON file."""
        with StorageEngine._lock:
            if os.path.exists(filepath):
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception as e:
                    print(f"[DB WARN] Failed reading {filepath}: {e}")
            return default if default is not None else {}

    def save_file(self, filepath: str, data: Dict[str, Any]):
        """Thread-safe atomic write to an arbitrary JSON file."""
        with StorageEngine._lock:
            dir_name = os.path.dirname(filepath)
            os.makedirs(dir_name, exist_ok=True)
            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w", encoding="utf-8",
                    dir=dir_name, delete=False, suffix=".tmp"
                ) as tmp:
                    json.dump(data, tmp, indent=2, ensure_ascii=False)
                    tmp_path = tmp.name
                os.replace(tmp_path, filepath)
            except Exception as e:
                print(f"[DB ERROR] Failed saving {filepath}: {e}")
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        pass
