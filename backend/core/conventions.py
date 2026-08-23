import uuid
import re

def generate_paper_id(title: str) -> str:
    """Generates a clean, normalized paper identifier prefixed with paper_."""
    # Convert title to lowercase, keep alphanumeric, trim to 30 chars
    clean_title = re.sub(r'[^a-z0-9\s]', '', title.lower()).strip()
    clean_title = re.sub(r'\s+', '_', clean_title)[:30].strip('_')
    if not clean_title:
        clean_title = str(uuid.uuid4())[:8]
    return f"paper_{clean_title}"

def generate_job_id() -> str:
    """Generates a unique execution job identifier prefixed with job_."""
    return f"job_{uuid.uuid4().hex[:16]}"

def generate_conversation_id() -> str:
    """Generates a unique persistent conversation identifier prefixed with conv_."""
    return f"conv_{uuid.uuid4().hex[:16]}"
