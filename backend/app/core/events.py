"""
Phase 9: Event-Driven Observability Framework
Defines structured events, typed models, and thread-safe dispatchers
for real backend LangGraph execution telemetry.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

from app.core.job_store import get_job_store, JobStatus

logger = logging.getLogger(__name__)


class EventTypes:
    NODE_STARTED = "node_started"
    NODE_COMPLETED = "node_completed"
    REFINEMENT = "refinement"
    RETRY = "retry"
    ERROR = "error"
    PIPELINE_STARTED = "pipeline_started"
    PIPELINE_COMPLETED = "pipeline_completed"
    PIPELINE_FAILED = "pipeline_failed"
    MASCOT_STATE = "mascot_state"


# Truthful, node-derived progress percentages
NODE_PROGRESS_MAP = {
    "initialized": 5.0,
    "ingestion_node": 15.0,
    "extraction_node": 30.0,
    "feasibility_node": 45.0,
    "adaptation_node": 50.0,
    "sequencing_node": 60.0,
    "specification_node": 70.0,
    "code_generation_node": 85.0,
    "repair_node": 88.0,
    "evaluation_node": 95.0,
    "completed": 100.0,
}

# Mapping of nodes to mascot states
NODE_MASCOT_MAP = {
    "ingestion_node": "reading",
    "extraction_node": "analyzing",
    "feasibility_node": "evaluating",
    "adaptation_node": "adapting",
    "sequencing_node": "planning",
    "specification_node": "architecting",
    "code_generation_node": "coding",
    "repair_node": "fixing",
    "evaluation_node": "testing",
    "completed": "ready",
    "failed": "sleeping",
}


class PipelineEvent(BaseModel):
    event_id: int
    job_id: str
    paper_id: str
    event: str
    node: Optional[str] = None
    status: str = "success"
    progress: float = 0.0
    timestamp: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


def emit_event(
    job_id: str,
    paper_id: str,
    event_type: str,
    node_name: Optional[str] = None,
    status: str = "success",
    progress: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> int:
    """
    Records an immutable, ordered event into SQLite via JobStore.
    Returns the sequential integer event_id.
    """
    if not job_id:
        return 0

    if progress is None and node_name in NODE_PROGRESS_MAP:
        progress = NODE_PROGRESS_MAP[node_name]
    elif progress is None:
        progress = 0.0

    meta = metadata.copy() if metadata else {}
    if node_name and "mascot_state" not in meta:
        meta["mascot_state"] = NODE_MASCOT_MAP.get(node_name, "working")

    job_store = get_job_store()
    event_id = job_store.record_event(
        job_id=job_id,
        paper_id=paper_id,
        event_type=event_type,
        node_name=node_name,
        status=status,
        progress=progress,
        metadata=meta
    )
    return event_id


def emit_node_start(
    job_id: str,
    paper_id: str,
    node_name: str,
    metadata: Optional[Dict[str, Any]] = None
) -> int:
    """Emits node_started event when a LangGraph node begins execution."""
    prog = NODE_PROGRESS_MAP.get(node_name, 0.0)
    return emit_event(
        job_id=job_id,
        paper_id=paper_id,
        event_type=EventTypes.NODE_STARTED,
        node_name=node_name,
        status="running",
        progress=prog,
        metadata=metadata
    )


def emit_node_complete(
    job_id: str,
    paper_id: str,
    node_name: str,
    metadata: Optional[Dict[str, Any]] = None
) -> int:
    """Emits node_completed event when a LangGraph node finishes successfully."""
    prog = NODE_PROGRESS_MAP.get(node_name, 0.0)
    return emit_event(
        job_id=job_id,
        paper_id=paper_id,
        event_type=EventTypes.NODE_COMPLETED,
        node_name=node_name,
        status="success",
        progress=prog,
        metadata=metadata
    )


def emit_refinement(
    job_id: str,
    paper_id: str,
    node_name: str,
    reason: str,
    adapted_fields: Optional[Dict[str, Any]] = None,
    attempt: int = 1
) -> int:
    """Emits refinement event when parameter adaptation modifies fields to fit constraints."""
    metadata = {
        "reason": reason,
        "adapted_fields": adapted_fields or {},
        "attempt": attempt,
        "action": "constraint_adaptation"
    }
    return emit_event(
        job_id=job_id,
        paper_id=paper_id,
        event_type=EventTypes.REFINEMENT,
        node_name=node_name,
        status="refining",
        progress=NODE_PROGRESS_MAP.get(node_name, 50.0),
        metadata=metadata
    )


def emit_retry(
    job_id: str,
    paper_id: str,
    node_name: str,
    attempt: int,
    max_retries: int,
    error_summary: str,
    metadata: Optional[Dict[str, Any]] = None
) -> int:
    """Emits retry event when a self-correcting repair loop triggers."""
    meta = metadata.copy() if metadata else {}
    meta.update({
        "attempt": attempt,
        "max_retries": max_retries,
        "error_summary": error_summary,
        "action": "reflexion_repair"
    })
    return emit_event(
        job_id=job_id,
        paper_id=paper_id,
        event_type=EventTypes.RETRY,
        node_name=node_name,
        status="retrying",
        progress=NODE_PROGRESS_MAP.get(node_name, 88.0),
        metadata=meta
    )


def emit_node_error(
    job_id: str,
    paper_id: str,
    node_name: str,
    error_message: str,
    metadata: Optional[Dict[str, Any]] = None
) -> int:
    """Emits error event when an unexpected exception or verification failure occurs."""
    meta = metadata.copy() if metadata else {}
    meta.update({"error": error_message})
    return emit_event(
        job_id=job_id,
        paper_id=paper_id,
        event_type=EventTypes.ERROR,
        node_name=node_name,
        status="failed",
        metadata=meta
    )
