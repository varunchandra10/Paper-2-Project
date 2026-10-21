import os
import json
import pytest
from fastapi.testclient import TestClient
from main import app
from app.core.job_store import JobStore, JobStatus, JobRecord, JobStoreDictWrapper

client = TestClient(app)


@pytest.fixture
def temp_job_store(tmp_path):
    db_file = str(tmp_path / "test_jobs.db")
    return JobStore(db_path=db_file)


def test_job_creation_and_retrieval(temp_job_store):
    store = temp_job_store
    record = store.create_job(paper_id="paper_123", initial_stage="queued", progress=10.0)
    assert record.job_id.startswith("job_")
    assert record.paper_id == "paper_123"
    assert record.status == JobStatus.QUEUED
    assert record.progress == 10.0

    # Retrieve by job_id
    fetched = store.get_job(record.job_id)
    assert fetched is not None
    assert fetched.job_id == record.job_id
    assert fetched.paper_id == "paper_123"

    # Retrieve by paper_id fallback
    fetched_by_paper = store.get_job("paper_123")
    assert fetched_by_paper is not None
    assert fetched_by_paper.job_id == record.job_id


def test_restart_persistence(tmp_path):
    db_file = str(tmp_path / "persistent_jobs.db")

    # Store 1: Create and update job
    store1 = JobStore(db_path=db_file)
    job = store1.create_job(paper_id="paper_persist", job_id="job_persist_1")
    store1.update_stage("job_persist_1", stage="parsing", progress=45.0, status=JobStatus.PROCESSING)

    # Store 2: Simulate complete server restart by opening fresh store on same DB
    store2 = JobStore(db_path=db_file)
    loaded = store2.get_job("job_persist_1")
    assert loaded is not None
    assert loaded.paper_id == "paper_persist"
    assert loaded.current_stage == "parsing"
    assert loaded.progress == 45.0
    assert loaded.status == JobStatus.PROCESSING


def test_zombie_job_recovery_on_restart(tmp_path):
    db_file = str(tmp_path / "zombie_jobs.db")
    store = JobStore(db_path=db_file)

    # Create 3 jobs left active when server dies
    store.create_job(paper_id="p1", job_id="j1", status=JobStatus.QUEUED)
    store.create_job(paper_id="p2", job_id="j2", status=JobStatus.PROCESSING)
    store.create_job(paper_id="p3", job_id="j3", status=JobStatus.RUNNING)
    # And one already completed
    completed_job = store.create_job(paper_id="p4", job_id="j4", status=JobStatus.COMPLETED)
    store.complete_job("j4", result={"success": True})

    # Simulate server recovery
    recovered_count = store.recover_stale_jobs(error_msg="Server restarted during execution")
    assert recovered_count == 3

    # Verify active jobs became failed
    for j_id in ["j1", "j2", "j3"]:
        rec = store.get_job(j_id)
        assert rec.status == JobStatus.FAILED
        assert rec.error == "Server restarted during execution"
        assert rec.current_stage == "server_restart_recovered"
        assert rec.completed_at is not None

    # Verify completed job was untouched
    c_rec = store.get_job("j4")
    assert c_rec.status == JobStatus.COMPLETED
    assert c_rec.result == {"success": True}


def test_cancellation_semantics(temp_job_store):
    store = temp_job_store
    job = store.create_job(paper_id="paper_cancel", job_id="job_cancel_1")
    assert not store.is_cancellation_requested("job_cancel_1")

    # Cancel active job
    cancelled = store.cancel_job("job_cancel_1")
    assert cancelled is True
    assert store.is_cancellation_requested("job_cancel_1")

    loaded = store.get_job("job_cancel_1")
    assert loaded.status == JobStatus.CANCELLED
    assert loaded.current_stage == "cancelled"

    # Cancelling already terminal job returns False
    second_cancel = store.cancel_job("job_cancel_1")
    assert second_cancel is False


def test_active_job_detection(temp_job_store):
    store = temp_job_store
    assert store.get_active_job_for_paper("p_active") is None

    # Create active job
    store.create_job(paper_id="p_active", job_id="job_act_1", status=JobStatus.PROCESSING)
    active = store.get_active_job_for_paper("p_active")
    assert active is not None
    assert active.job_id == "job_act_1"

    # Complete it
    store.complete_job("job_act_1", result={"ok": True})
    assert store.get_active_job_for_paper("p_active") is None


def test_dict_wrapper_compatibility(temp_job_store):
    store = temp_job_store
    wrapper = JobStoreDictWrapper(store)

    # Dictionary assignment
    wrapper["dict_job_1"] = {
        "paper_id": "paper_dict",
        "status": "processing",
        "progress": 35.0,
        "current_stage": "extracting"
    }

    # Contains check
    assert "dict_job_1" in wrapper
    assert "non_existent" not in wrapper

    # Subscript access
    item = wrapper["dict_job_1"]
    assert item["job_id"] == "dict_job_1"
    assert item["paper_id"] == "paper_dict"
    assert item["status"] == "processing"
    assert item["progress"] == 35.0

    # Updating via wrapper
    wrapper["dict_job_1"] = {
        "paper_id": "paper_dict",
        "status": "completed",
        "progress": 100.0,
        "result": {"accuracy": 0.95}
    }
    assert wrapper["dict_job_1"]["status"] == "completed"
    assert wrapper["dict_job_1"]["result"] == {"accuracy": 0.95}


def test_duplicate_submission_api_safety():
    from app.core.job_store import get_job_store
    store = get_job_store()

    paper_id = "paper_dup_test"
    # Create an active job in progress
    active_job = store.create_job(paper_id=paper_id, job_id="job_active_dup", status=JobStatus.RUNNING)

    # Submitting another analysis while active returns the existing job
    resp = client.post("/api/v1/analyze", json={"paper_id": paper_id})
    assert resp.status_code == 200
    data = resp.json()
    assert data["job_id"] == "job_active_dup"
    assert "already in progress" in data.get("message", "")

    # Once cancelled or completed, submission creates a new job
    store.cancel_job("job_active_dup")
    resp_after = client.post("/api/v1/analyze", json={"paper_id": paper_id})
    assert resp_after.status_code == 200
    data_after = resp_after.json()
    assert data_after["job_id"] != "job_active_dup"
    assert data_after["job_id"].startswith("job_")


def test_cancel_api_endpoint():
    from app.core.job_store import get_job_store
    store = get_job_store()

    job = store.create_job(paper_id="paper_cancel_api", job_id="job_cancel_api_1", status=JobStatus.QUEUED)

    # Cancel via API
    resp = client.post(f"/api/v1/analyze/{job.job_id}/cancel")
    assert resp.status_code == 200
    data = resp.json()
    assert data["job_id"] == job.job_id
    assert data["cancelled"] is True
    assert data["status"] == "cancelled"

    # Verify status in database
    status_resp = client.get(f"/api/v1/analyze/{job.job_id}/status")
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "cancelled"


def test_truthful_sse_streaming_completed():
    from app.core.job_store import get_job_store
    store = get_job_store()

    job_id = "job_sse_comp"
    store.create_job(paper_id="paper_sse_1", job_id=job_id, status=JobStatus.COMPLETED)
    store.complete_job(job_id, result={"done": True})

    with client.stream("GET", f"/api/v1/stream/{job_id}") as response:
        assert response.status_code == 200
        content = "".join([chunk.decode("utf-8") if isinstance(chunk, bytes) else chunk for chunk in response.iter_raw()])
        assert "event: COMPLETED" in content or "event: completed" in content
        assert "event: mascot-state\ndata: ready" in content


def test_truthful_sse_streaming_failed():
    from app.core.job_store import get_job_store
    store = get_job_store()

    job_id = "job_sse_fail"
    store.create_job(paper_id="paper_sse_2", job_id=job_id, status=JobStatus.PROCESSING)
    store.fail_job(job_id, error="Simulated OOM failure")

    with client.stream("GET", f"/api/v1/stream/{job_id}") as response:
        assert response.status_code == 200
        content = "".join([chunk.decode("utf-8") if isinstance(chunk, bytes) else chunk for chunk in response.iter_raw()])
        assert "event: ERROR" in content or "event: failed" in content
        assert "Simulated OOM failure" in content
        assert "event: mascot-state\ndata: sleeping" in content
