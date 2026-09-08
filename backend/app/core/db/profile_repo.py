import os
import json
import datetime
from typing import Optional, Dict, Any
from app.core.config import settings
from app.core.db.storage_engine import StorageEngine


class ProfileRepository:
    """Repository managing user authentication records and standalone user profiles."""

    def __init__(self, storage: StorageEngine):
        self.storage = storage

    def get_user_by_email(self, email: str) -> Optional[dict]:
        """Looks up a user record by email in the global index."""
        data = self.storage.load_index()
        users = data.get("users", {})
        for uid, u in users.items():
            if u.get("email") == email:
                return u
        return None

    def create_user(self, email: str, password_hash: str, full_name: str = "") -> dict:
        """Creates a new registered user in the local index."""
        data = self.storage.load_index()
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
        self.storage.save_index(data)
        self.sync_user_registry_webhook(email, full_name)
        return user_data

    def sync_user_registry_webhook(self, email: str, username: str):
        """Syncs user email and username to external Webhook API if configured."""
        if settings.USER_REGISTRY_WEBHOOK and "your_" not in settings.USER_REGISTRY_WEBHOOK.lower():
            try:
                import requests
                requests.post(
                    settings.USER_REGISTRY_WEBHOOK,
                    json={
                        "email": email,
                        "username": username,
                        "timestamp": datetime.datetime.now().isoformat()
                    },
                    timeout=5
                )
                print(f"[DB WEBHOOK] Synced user ({email}) to registry webhook API.")
            except Exception as w_err:
                print(f"[DB WEBHOOK WARN] Webhook sync notice: {w_err}")

    def get_standalone_user_profile(self) -> dict:
        """Loads user profile directly from storage/history/user_profile.json."""
        profile_file = settings.USER_PROFILE_FILE
        default_profile = {
            "user_id": "usr_1",
            "username": "Varun Chandra",
            "email": "varunchandra10@gmail.com",
            "dob": "2000-01-01",
            "age": "26",
            "phoneNumber": "+1 (555) 019-2834",
            "projectPath": settings.BASE_DIR,
            "ollamaLink": "",
            "avatarId": "mr-nerdy"
        }
        return self.storage.load_file(profile_file, default=default_profile)

    def save_standalone_user_profile(self, profile_dict: dict) -> dict:
        """Saves user profile directly into storage/history/user_profile.json."""
        current = self.get_standalone_user_profile()
        for k, v in profile_dict.items():
            if v is not None:
                current[k] = v
        current["updated_at"] = datetime.datetime.now().isoformat()
        
        self.storage.save_file(settings.USER_PROFILE_FILE, current)
        print(f"[DB] Saved user profile to '{settings.USER_PROFILE_FILE}'.")
            
        email = current.get("email", "")
        username = current.get("username") or current.get("full_name") or ""
        self.sync_user_registry_webhook(email, username)
        return current

    def update_user_profile(self, user_id: str, profile_dict: dict) -> dict:
        """Updates user profile details in JSON database and user_profile.json."""
        data = self.storage.load_index()
        if "users" not in data:
            data["users"] = {}
        
        user_data = data["users"].get(user_id) or {}
        user_data["id"] = user_id
        for k, v in profile_dict.items():
            if v is not None:
                user_data[k] = v
        user_data["updated_at"] = datetime.datetime.now().isoformat()
        
        data["users"][user_id] = user_data
        self.storage.save_index(data)
        
        return self.save_standalone_user_profile(profile_dict)
