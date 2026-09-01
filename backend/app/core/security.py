import hashlib
import datetime
from typing import Optional, Any
from app.core.config import settings

def hash_password(password: str) -> str:
    """Generates a secure SHA-256 password hash."""
    salted = f"{settings.SECRET_KEY}:{password}"
    return hashlib.sha256(salted.encode('utf-8')).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a stored hash."""
    return hash_password(plain_password) == hashed_password
