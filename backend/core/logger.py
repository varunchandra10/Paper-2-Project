import logging
import json
import time
from typing import Any, Dict, Optional

import os

backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
log_file_path = os.path.join(backend_dir, "backend_observability.log")

# Set up logging level and formats explicitly (basicConfig may be ignored in Jupyter)
logger = logging.getLogger("Observability")
logger.setLevel(logging.INFO)

# Prevent duplicate handlers
if not logger.handlers:
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    
    # File Handler
    file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Stream Handler
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)



def log_observability_event(
    event_type: str,
    paper_id: Optional[str] = None,
    job_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
    model: Optional[str] = None,
    latency_ms: Optional[float] = None,
    errors: Optional[str] = None,
    pipeline_state: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """Logs a structured observability event for analytics and tracing (Day 48)."""
    payload = {
        "event_type": event_type,
        "timestamp": time.time(),
        "paper_id": paper_id,
        "job_id": job_id,
        "conversation_id": conversation_id,
        "model": model,
        "latency_ms": latency_ms,
        "errors": errors,
        "pipeline_state": pipeline_state,
        "metadata": metadata or {}
    }
    # Clean up None values for compact logs
    filtered_payload = {k: v for k, v in payload.items() if v is not None}
    
    # Write JSON string to logger
    logger.info(f"[OBSERVABILITY] {json.dumps(filtered_payload, ensure_ascii=False)}")
