import os
import hashlib

def hash_password(password: str) -> str:
    """Generates a cryptographically secure hash of a password using PBKDF2 HMAC SHA-256

    with a random 16-byte salt and 100,000 iterations.
    """
    if not password:
        raise ValueError("Password cannot be empty")
        
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return f"{salt.hex()}${key.hex()}"

def verify_password(stored_hash: str, password: str) -> bool:
    """Verifies a password against a stored PBKDF2 signature."""
    if not stored_hash or not password:
        return False
        
    try:
        salt_hex, key_hex = stored_hash.split('$')
        salt = bytes.fromhex(salt_hex)
        key = bytes.fromhex(key_hex)
        
        # Hash input password using the extracted salt
        new_key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return new_key == key
    except Exception:
        return False
