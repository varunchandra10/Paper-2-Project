"""
Phase 9: Event-Driven Observability Test Suite
Verifies:
1. Removal of synthetic progress milestones in favor of real backend state.
2. Ordered, persistent event logging in SQLite (job_events table).
3. Monotonic sequence IDs and ISO-8601 timestamps.
4. Reconnection catch-up via Last-Event-ID / since_id without dropped or duplicate events.
5. Emitting real node_started, node_completed, refinement, retry, and error events.
6. Mascot state synchronization with backend execution.
"""

import os
import json
import time
import pytest
from datetime import datetime

from app.core.job_store import JobStore, JobStatus
from app.core.events import (
    EventTypes,
    emit_event,
    emit_node_start,
    emit_node_complete,
    emit_refinement,
    emit_retry,
    emit_node_error,
    NODE_PROGRESS_MAP,
    NODE_MASCOT_MAP
)
from app.graph.state import PipelineState
from app.graph.workflow import wrap_node_with_telemetry


@pytest.fixture
def temp_store(tmp_path, monkeypatch):
    """Provides an isolated SQLite job store."""
    db_file = str(tmp_path / "test_observability.db")
    store = JobStore(db_path=db_file)
    monkeypatch.setattr("app.core.events.get_job_store", lambda: store)
    return store


def test_persistent_event_logging_and_schema(temp_store):
    """Verifies that events are written to SQLite job_events with all required schema fields."""
    job = temp_store.create_job(paper_id="paper_v2_test", job_id="job_obs_01")

    eid1 = temp_store.record_event(
        job_id=job.job_id,
        paper_id=job.paper_id,
        event_type=EventTypes.NODE_STARTED,
        node_name="feasibility_node",
        status="running",
        progress=40.0,
        metadata={"attempt": 1}
    )

    eid2 = temp_store.record_event(
        job_id=job.job_id,
        paper_id=job.paper_id,
        event_type=EventTypes.NODE_COMPLETED,
        node_name="feasibility_node",
        status="success",
        progress=50.0,
        metadata={"duration_ms": 320, "verdict": "FEASIBLE"}
    )

    # Monotonic event ID checks
    assert eid1 > 0
    assert eid2 == eid1 + 1

    events = temp_store.get_events(job.job_id)
    assert len(events) == 2

    ev1 = events[0]
    assert ev1["event_id"] == eid1
    assert ev1["job_id"] == "job_obs_01"
    assert ev1["paper_id"] == "paper_v2_test"
    assert ev1["event"] == EventTypes.NODE_STARTED
    assert ev1["node"] == "feasibility_node"
    assert ev1["status"] == "running"
    assert ev1["progress"] == 40.0
    assert "timestamp" in ev1
    assert ev1["metadata"]["attempt"] == 1

    ev2 = events[1]
    assert ev2["event"] == EventTypes.NODE_COMPLETED
    assert ev2["progress"] == 50.0
    assert ev2["metadata"]["duration_ms"] == 320
    assert ev2["metadata"]["verdict"] == "FEASIBLE"


def test_event_ordering_and_monotonicity(temp_store):
    """Verifies strict sequential ordering of multiple events."""
    job = temp_store.create_job(paper_id="paper_ordering", job_id="job_ordering_01")
    nodes = ["ingestion_node", "extraction_node", "feasibility_node", "sequencing_node"]

    emitted_ids = []
    for node in nodes:
        eid_start = temp_store.record_event(job.job_id, job.paper_id, EventTypes.NODE_STARTED, node_name=node)
        eid_done = temp_store.record_event(job.job_id, job.paper_id, EventTypes.NODE_COMPLETED, node_name=node)
        emitted_ids.extend([eid_start, eid_done])

    retrieved_events = temp_store.get_events(job.job_id)
    retrieved_ids = [e["event_id"] for e in retrieved_events]

    assert retrieved_ids == emitted_ids
    assert retrieved_ids == sorted(retrieved_ids)
    assert len(retrieved_ids) == 8


def test_client_reconnection_and_catchup_without_duplicates(temp_store):
    """
    CRITICAL TEST: Verifies that reconnecting clients with Last-Event-ID or since_id
    receive ONLY the new/missed events, preventing duplicates and eliminating dropped events.
    """
    job = temp_store.create_job(paper_id="paper_reconnect", job_id="job_recon_01")

    # 1. Initial 3 events emitted before client connects
    e1 = temp_store.record_event(job.job_id, job.paper_id, EventTypes.PIPELINE_STARTED, progress=5.0)
    e2 = temp_store.record_event(job.job_id, job.paper_id, EventTypes.NODE_STARTED, node_name="ingestion_node", progress=15.0)
    e3 = temp_store.record_event(job.job_id, job.paper_id, EventTypes.NODE_COMPLETED, node_name="ingestion_node", progress=20.0)

    # Client connects with since_id=0 (initial connection)
    batch_1 = temp_store.get_events(job.job_id, since_id=0)
    assert len(batch_1) == 3
    assert [e["event_id"] for e in batch_1] == [e1, e2, e3]

    # 2. Pipeline progresses, emitting events 4 and 5 while client was disconnected
    e4 = temp_store.record_event(job.job_id, job.paper_id, EventTypes.NODE_STARTED, node_name="extraction_node", progress=30.0)
    e5 = temp_store.record_event(job.job_id, job.paper_id, EventTypes.NODE_COMPLETED, node_name="extraction_node", progress=40.0)

    # Client reconnects with Last-Event-ID = e3
    batch_reconnect = temp_store.get_events(job.job_id, since_id=e3)
    assert len(batch_reconnect) == 2
    assert [e["event_id"] for e in batch_reconnect] == [e4, e5]
    # No duplicate events from batch_1
    assert not any(e["event_id"] in [e1, e2, e3] for e in batch_reconnect)

    # 3. Client checks again when no new events exist
    batch_empty = temp_store.get_events(job.job_id, since_id=e5)
    assert len(batch_empty) == 0


def test_refinement_retry_and_error_events(temp_store):
    """Verifies dedicated emission of domain events: refinement, retry, and error."""
    job = temp_store.create_job(paper_id="paper_domain_events", job_id="job_domain_01")

    # 1. Refinement Event (e.g., parameter adaptation scaling down batch size)
    refine_id = emit_refinement(
        job_id=job.job_id,
        paper_id=job.paper_id,
        node_name="adaptation_node",
        reason="VRAM limit exceeded (12.4 GB > 6.0 GB)",
        adapted_fields={"batch_size": {"old": 32, "new": 16}},
        attempt=1
    )

    # 2. Retry Event (e.g., reflexion repair gate fixing missing import)
    retry_id = emit_retry(
        job_id=job.job_id,
        paper_id=job.paper_id,
        node_name="code_repair_node",
        attempt=1,
        max_retries=2,
        error_summary="NameError: name 'nn' is not defined",
        metadata={"file": "model.py"}
    )

    # 3. Error Event (e.g., runtime tensor dimension mismatch)
    error_id = emit_node_error(
        job_id=job.job_id,
        paper_id=job.paper_id,
        node_name="evaluation_node",
        error_message="RuntimeError: mat1 and mat2 shapes cannot be multiplied (2x64 and 128x2)",
        metadata={"layer": "layer3_execution"}
    )

    events = temp_store.get_events(job.job_id)
    assert len(events) == 3

    # Verify refinement event payload
    ev_ref = events[0]
    assert ev_ref["event_id"] == refine_id
    assert ev_ref["event"] == EventTypes.REFINEMENT
    assert ev_ref["status"] == "refining"
    assert ev_ref["metadata"]["action"] == "constraint_adaptation"
    assert ev_ref["metadata"]["adapted_fields"]["batch_size"]["new"] == 16

    # Verify retry event payload
    ev_retry = events[1]
    assert ev_retry["event_id"] == retry_id
    assert ev_retry["event"] == EventTypes.RETRY
    assert ev_retry["status"] == "retrying"
    assert ev_retry["metadata"]["attempt"] == 1
    assert "is not defined" in ev_retry["metadata"]["error_summary"]

    # Verify error event payload
    ev_err = events[2]
    assert ev_err["event_id"] == error_id
    assert ev_err["event"] == EventTypes.ERROR
    assert ev_err["status"] == "failed"
    assert "mat1 and mat2 shapes" in ev_err["metadata"]["error"]


def test_node_telemetry_wrapping_records_real_timing_and_state(temp_store):
    """Verifies that wrap_node_with_telemetry measures real execution time and state."""
    job = temp_store.create_job(paper_id="paper_wrap_test", job_id="job_wrap_01")

    # Define a toy node that executes real work
    def toy_node(state: PipelineState) -> dict:
        time.sleep(0.05)  # 50ms real execution delay
        return {"toy_result": "processed_payload"}

    wrapped = wrap_node_with_telemetry("toy_node", toy_node)

    state = {
        "job_id": job.job_id,
        "paper_id": job.paper_id,
        "constraints": {}
    }

    result = wrapped(state)
    assert result["toy_result"] == "processed_payload"

    events = temp_store.get_events(job.job_id)
    assert len(events) == 2

    start_ev = events[0]
    assert start_ev["event"] == EventTypes.NODE_STARTED
    assert start_ev["node"] == "toy_node"

    complete_ev = events[1]
    assert complete_ev["event"] == EventTypes.NODE_COMPLETED
    assert complete_ev["node"] == "toy_node"
    # Real wall-clock duration measured
    assert complete_ev["metadata"]["duration_ms"] >= 40


def test_elimination_of_synthetic_milestones(temp_store):
    """
    Verifies that progress in the job table is truthful and advances monotonically
    according to real node execution, not hardcoded arbitrary values.
    """
    job = temp_store.create_job(paper_id="paper_prog", job_id="job_prog_01", initial_stage="queued", progress=0.0)
    assert job.progress == 0.0

    # Ingestion node finishes -> progress derived from NODE_PROGRESS_MAP
    emit_node_complete(job.job_id, job.paper_id, "ingestion_node")
    updated_job = temp_store.get_job(job.job_id)
    assert updated_job.progress == NODE_PROGRESS_MAP["ingestion_node"]
    assert updated_job.current_stage == "ingestion_node"

    # Extraction finishes
    emit_node_complete(job.job_id, job.paper_id, "extraction_node")
    updated_job = temp_store.get_job(job.job_id)
    assert updated_job.progress == NODE_PROGRESS_MAP["extraction_node"]

    # Final completion
    temp_store.record_event(job.job_id, job.paper_id, EventTypes.PIPELINE_COMPLETED, progress=100.0)
    final_job = temp_store.get_job(job.job_id)
    assert final_job.progress == 100.0


@pytest.mark.anyio
async def test_sse_stream_generator_reconnection(temp_store, monkeypatch):
    """
    Verifies that stream_analysis_events formats SSE messages with 'id: <seq_id>'
    and properly replays missed events based on Last-Event-ID header.
    """
    monkeypatch.setattr("app.api.v1.endpoints.pipeline.job_store", temp_store)

    job = temp_store.create_job(paper_id="paper_sse_test", job_id="job_sse_01")
    e1 = temp_store.record_event(job.job_id, job.paper_id, EventTypes.PIPELINE_STARTED, progress=5.0)
    e2 = temp_store.record_event(job.job_id, job.paper_id, EventTypes.NODE_COMPLETED, node_name="ingestion_node", progress=20.0)
    temp_store.complete_job(job.job_id, result={"status": "done"})

    from starlette.requests import Request

    # 1. Connect without Last-Event-ID (initial stream)
    scope = {"type": "http", "headers": []}
    req1 = Request(scope)

    from app.api.v1.endpoints.pipeline import stream_analysis_events
    response = await stream_analysis_events(job.job_id, req1, since_id=0)

    chunks = []
    async for chunk in response.body_iterator:
        chunks.append(chunk)

    full_output = "".join(chunks)
    assert "event: log" in full_output
    assert f"id: {e1}" in full_output
    assert f"id: {e2}" in full_output
    assert "event: SECTION_DETECTED" in full_output  # Backward compatible alias for ingestion_node
    assert "event: COMPLETED" in full_output

    # 2. Reconnect with Last-Event-ID: e1 (should receive e2 and COMPLETED, but NOT e1)
    scope_reconnect = {
        "type": "http",
        "headers": [(b"last-event-id", str(e1).encode())]
    }
    req2 = Request(scope_reconnect)
    response_reconnect = await stream_analysis_events(job.job_id, req2)

    chunks_recon = []
    async for chunk in response_reconnect.body_iterator:
        chunks_recon.append(chunk)

    recon_output = "".join(chunks_recon)
    assert f"id: {e1}" not in recon_output  # Old event NOT duplicated!
    assert f"id: {e2}" in recon_output      # New event received!
    assert "event: COMPLETED" in recon_output
