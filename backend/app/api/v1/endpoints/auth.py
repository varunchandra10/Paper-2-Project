from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
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


class UserProfileUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    dob: Optional[str] = None
    age: Optional[str] = None
    phoneNumber: Optional[str] = None
    projectPath: Optional[str] = None
    ollamaLink: Optional[str] = None
    avatarId: Optional[str] = None


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
    """Local developer profile login / creation."""
    existing = db.get_user_by_email(req.email)
    if not existing:
        user = db.create_user(email=req.email, password_hash="local_dev", full_name=req.username)
        user_id = user["id"]
    else:
        user_id = existing["id"]
        db.update_user_profile(user_id, {"username": req.username, "email": req.email})

    return {
        "status": "success",
        "user_id": user_id,
        "username": req.username,
        "email": req.email
    }


@router.get("/profile")
@router.get("/user/profile")
def get_user_profile(user_id: str = "usr_1"):
    """Gets persistent user profile from database."""
    data = db._load_fallback()
    users = data.get("users", {})
    user = users.get(user_id) or next(iter(users.values()), None)
    if not user:
        return {
            "user_id": user_id,
            "username": "Varun Chandra",
            "email": "varunchandra10@gmail.com",
            "dob": "2000-01-01",
            "age": "26",
            "phoneNumber": "+1 (555) 019-2834",
            "projectPath": "c:\\Users\\kvcsu_ht23nk8\\OneDrive\\Desktop\\all_Projects\\Projects\\agentic_projects\\Paper-2-Project",
            "ollamaLink": "http://localhost:11434",
            "avatarId": "mr-nerdy"
        }
    return {
        "user_id": user.get("id", user_id),
        "username": user.get("username") or user.get("full_name") or "Varun Chandra",
        "email": user.get("email") or "varunchandra10@gmail.com",
        "dob": user.get("dob"),
        "age": user.get("age"),
        "phoneNumber": user.get("phoneNumber") or user.get("phone_number"),
        "projectPath": user.get("projectPath") or user.get("project_path"),
        "ollamaLink": user.get("ollamaLink") or user.get("ollama_link"),
        "avatarId": user.get("avatarId") or user.get("avatar_id") or "mr-nerdy"
    }


@router.put("/profile")
@router.put("/user/profile")
@router.post("/user/profile")
def update_user_profile_endpoint(req: UserProfileUpdate, user_id: str = "usr_1"):
    """Persists extended user profile into JSON database and exports to user_profiles.xlsx spreadsheet."""
    profile_dict = req.model_dump(exclude_unset=True)
    updated = db.update_user_profile(user_id, profile_dict)
    return {
        "status": "success",
        "message": "User profile saved and exported to user_profiles.xlsx",
        "user": updated
    }
