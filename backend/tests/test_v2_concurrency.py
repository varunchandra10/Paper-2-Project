"""
Phase 11 (Testing V2): Concurrency and Thread Safety Test Suite.

Verifies:
- Thread-safe job creation and status transitions in SQLite WAL mode.
- High-concurrency event logging across multiple threads without database locks.
- Stream isolation: Concurrent jobs do not leak events or manifests to other jobs.
"""

import threading
import pytest
from app.core.job_store import JobStore, JobStatus
from app.core.events import EventTypes


def test_concurrent_multithreaded_job_creation(tmp_path):
    """
    Concurrency Test: 20 threads simultaneously creating and completing jobs in SQLite.
    Verifies that WAL mode prevents 'database is locked' errors.
    """
    db_file = tmp_path / "concurrent_jobs.db"
    store = JobStore(db_path=str(db_file))

    num_threads = 20
    errors = []

    def worker(worker_id):
        try:
            job_id = f"job_thread_{worker_id}"
            paper_id = f"paper_thread_{worker_id}"
            store.create_job(paper_id=paper_id, job_id=job_id)
            store.update_stage(job_id, stage="running", progress=50.0, status=JobStatus.RUNNING)
            store.complete_job(job_id, result={"worker": worker_id})
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == [], f"Encountered threading errors: {errors}"
    jobs = store.list_jobs(limit=100)
    assert len(jobs) == num_threads
    assert all(j.status == JobStatus.COMPLETED for j in jobs)


def test_concurrent_event_logging_cross_job_isolation(tmp_path):
    """
    Concurrency Test: Multiple threads logging events concurrently to different jobs.
    Verifies that events are monotonically ordered per job and strictly isolated.
    """
    db_file = tmp_path / "concurrent_events.db"
    store = JobStore(db_path=str(db_file))

    num_jobs = 10
    events_per_job = 15

    for j in range(num_jobs):
        store.create_job(paper_id=f"paper_iso_{j}", job_id=f"job_iso_{j}")

    errors = []

    def emit_worker(job_idx):
        try:
            job_id = f"job_iso_{job_idx}"
            paper_id = f"paper_iso_{job_idx}"
            for step in range(events_per_job):
                store.record_event(
                    job_id=job_id,
                    paper_id=paper_id,
                    event_type=EventTypes.NODE_STARTED,
                    node_name=f"node_{step}",
                    status="success",
                    progress=(step / events_per_job) * 100.0,
                    metadata={"step": step}
                )
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=emit_worker, args=(i,)) for i in range(num_jobs)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == []

    # Check each job's isolation and event monotonicity
    for j in range(num_jobs):
        job_id = f"job_iso_{j}"
        events = store.get_events(job_id)
        assert len(events) == events_per_job
        assert all(e["job_id"] == job_id for e in events)

        # Monotonically increasing event_id
        event_ids = [e["event_id"] for e in events]
        assert event_ids == sorted(event_ids)
