import os
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.config import settings
from app.core.database import ChatDatabase
from app.core.security import hash_password, verify_password

router = APIRouter()
db = ChatDatabase()
db.initialize_db()


class UserRegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str = ""


class UserLoginRequest(BaseModel):
    email: str
    password: str


class LocalLoginRequest(BaseModel):
    username: str
    email: str


class VerifyKeyRequest(BaseModel):
    provider: str  # 'groq' | 'openrouter'
    api_key: str


class SetupWizardRequest(BaseModel):
    username: str
    email: str
    subscribed: Optional[bool] = False
    projectPath: Optional[str] = None
    allowCodeExecution: Optional[bool] = True
    detectHardware: Optional[bool] = True
    ollamaEnabled: Optional[bool] = True
    ollamaLink: Optional[str] = ""
    groqApiKey: Optional[str] = None
    openrouterApiKey: Optional[str] = None
    rememberDevice: Optional[bool] = True
    avatarId: Optional[str] = "mr-nerdy"
    deviceInfo: Optional[dict] = None


class UserProfileUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    dob: Optional[str] = None
    age: Optional[str] = None
    phoneNumber: Optional[str] = None
    projectPath: Optional[str] = None
    ollamaLink: Optional[str] = None
    avatarId: Optional[str] = None
    groqApiKey: Optional[str] = None
    openrouterApiKey: Optional[str] = None
    allowCodeExecution: Optional[bool] = None
    rememberDevice: Optional[bool] = None


@router.post("/register")
def register_user(req: UserRegisterRequest):
    existing = db.get_user_by_email(req.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered.")
    pwd_hash = hash_password(req.password)
    user = db.create_user(email=req.email, password_hash=pwd_hash, full_name=req.full_name)
    return {"message": "User registered successfully", "user_id": user["id"]}


@router.post("/login")
def login_user(req: UserLoginRequest):
    user = db.get_user_by_email(req.email)
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    return {"message": "Login successful", "user": {"id": user["id"], "email": user["email"]}}


@router.post("/local-login")
def local_login(req: LocalLoginRequest):
    """Local developer profile login / creation and Google Sheets webhook sync."""
    existing = db.get_user_by_email(req.email)
    if not existing:
        user = db.create_user(email=req.email, password_hash="local_dev", full_name=req.username)
        user_id = user["id"]
    else:
        user_id = existing["id"]
        db.update_user_profile(user_id, {"username": req.username, "email": req.email})

    db.save_standalone_user_profile({
        "user_id": user_id,
        "username": req.username,
        "email": req.email
    })

    return {
        "status": "success",
        "user_id": user_id,
        "username": req.username,
        "email": req.email
    }


@router.post("/verify-key")
def verify_api_key(req: VerifyKeyRequest):
    """Verifies user-provided Groq or OpenRouter API key without generating completions."""
    import httpx
    provider = req.provider.lower().strip()
    key = req.api_key.strip()

    if not key:
        return {"valid": False, "provider": provider, "message": "API key cannot be empty"}

    if provider == "groq":
        try:
            resp = httpx.get(
                "https://api.groq.com/openai/v1/models",
                headers={"Authorization": f"Bearer {key}"},
                timeout=4.0
            )
            if resp.status_code == 200:
                return {
                    "valid": True,
                    "provider": "groq",
                    "message": "Groq LPU API Key verified successfully!"
                }
            elif resp.status_code in [401, 403]:
                return {
                    "valid": False,
                    "provider": "groq",
                    "message": "Invalid Groq API Key. Please verify your token."
                }
            return {
                "valid": False,
                "provider": "groq",
                "message": f"Groq Gateway returned HTTP {resp.status_code}"
            }
        except Exception as e:
            return {"valid": False, "provider": "groq", "message": f"Connection error: {str(e)}"}

    elif provider == "openrouter":
        try:
            resp = httpx.get(
                "https://openrouter.ai/api/v1/auth/key",
                headers={"Authorization": f"Bearer {key}"},
                timeout=4.0
            )
            if resp.status_code == 200:
                data = resp.json().get("data", {})
                usage = data.get("usage", 0.0)
                limit = data.get("limit")
                limit_str = f" / ${limit}" if limit else ""
                return {
                    "valid": True,
                    "provider": "openrouter",
                    "message": f"OpenRouter Key verified! (Usage: ${usage:.4f}{limit_str})",
                    "data": data
                }
            elif resp.status_code in [401, 403]:
                return {
                    "valid": False,
                    "provider": "openrouter",
                    "message": "Invalid OpenRouter API Key. Please verify your token."
                }
            return {
                "valid": False,
                "provider": "openrouter",
                "message": f"OpenRouter Gateway returned HTTP {resp.status_code}"
            }
        except Exception as e:
            return {"valid": False, "provider": "openrouter", "message": f"Connection error: {str(e)}"}

    return {"valid": False, "provider": provider, "message": f"Unsupported provider: {provider}"}


@router.get("/check-ollama")
def check_ollama_status():
    """Checks if local Ollama daemon is running on localhost:11434."""
    import httpx
    try:
        resp = httpx.get("http://localhost:11434/api/tags", timeout=1.5)
        if resp.status_code == 200:
            models_data = resp.json().get("models", [])
            model_names = [m.get("name") for m in models_data]
            return {
                "running": True,
                "models": model_names,
                "count": len(model_names),
                "message": f"Local Ollama online ({len(model_names)} models found)"
            }
    except Exception:
        pass

    return {
        "running": False,
        "models": [],
        "count": 0,
        "message": "Ollama daemon not detected on http://localhost:11434"
    }


@router.post("/setup-wizard")
def complete_setup_wizard(req: SetupWizardRequest):
    """Complete first-run onboarding wizard: identity, permissions, BYOK, and local hardware."""
    existing = db.get_user_by_email(req.email)
    if not existing:
        user = db.create_user(email=req.email, password_hash="local_dev", full_name=req.username)
        user_id = user["id"]
    else:
        user_id = existing["id"]
        db.update_user_profile(user_id, {"username": req.username, "email": req.email})

    profile_payload = {
        "user_id": user_id,
        "username": req.username,
        "email": req.email,
        "subscribed": req.subscribed or False,
        "projectPath": req.projectPath or None,
        "allowCodeExecution": req.allowCodeExecution,
        "detectHardware": req.detectHardware,
        "ollamaEnabled": req.ollamaEnabled,
        "ollamaLink": req.ollamaLink or "",
        "groqApiKey": req.groqApiKey or None,
        "openrouterApiKey": req.openrouterApiKey or None,
        "rememberDevice": req.rememberDevice,
        "avatarId": req.avatarId or "mr-nerdy",
        "deviceInfo": req.deviceInfo or {}
    }

    saved = db.save_standalone_user_profile(profile_payload)
    return {
        "status": "success",
        "message": "Onboarding setup completed successfully!",
        "user_id": user_id,
        "user": saved
    }


@router.post("/reset-session")
def reset_session():
    """Wipes local user profile session and forces First-Run Onboarding Setup Wizard."""
    profile_file = settings.USER_PROFILE_FILE
    if os.path.exists(profile_file):
        try:
            os.remove(profile_file)
        except Exception:
            pass
    return {"status": "success", "message": "User profile session cleared."}


@router.get("/profile")
@router.get("/user/profile")
def get_user_profile(user_id: str = "usr_1"):
    """Gets persistent user profile enriched with live console metrics from OpenRouter and Groq."""
    from app.core.quota_tracker import quota_tracker
    profile = db.get_standalone_user_profile()
    try:
        profile["server_metrics"] = quota_tracker.fetch_live_server_metrics()
        profile["limits"] = quota_tracker.get_limits_summary()
    except Exception:
        profile["server_metrics"] = {}
        profile["limits"] = {}
    return profile


@router.put("/profile")
@router.put("/user/profile")
@router.post("/user/profile")
def update_user_profile_endpoint(req: UserProfileUpdate, user_id: str = "usr_1"):
    """Persists user profile directly into storage/history/user_profile.json."""
    profile_dict = req.model_dump(exclude_unset=True)
    updated = db.save_standalone_user_profile(profile_dict)
    return {
        "status": "success",
        "message": "User profile saved to user_profile.json",
        "user": updated
    }
