import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_analyze_and_status_endpoints():
    # 1. Test POST /api/v1/analyze
    resp = client.post("/api/v1/analyze", json={"paper_id": "test_paper_1", "constraints": {}})
    assert resp.status_code == 200
    data = resp.json()
    assert "job_id" in data
    assert data["status"] == "queued"
    job_id = data["job_id"]

    # 2. Test GET /api/v1/analyze/{job_id}/status
    status_resp = client.get(f"/api/v1/analyze/{job_id}/status")
    assert status_resp.status_code == 200
    assert status_resp.json()["job_id"] == job_id

    # 3. Test GET /api/v1/extraction/status/{job_id} (alias)
    alias_resp = client.get(f"/api/v1/extraction/status/{job_id}")
    assert alias_resp.status_code == 200
    assert alias_resp.json()["job_id"] == job_id


def test_trigger_analysis_legacy_alias():
    resp = client.post("/api/v1/history/test_paper_legacy/trigger_analysis?model_name=gemini-2.5-flash")
    assert resp.status_code == 200
    data = resp.json()
    assert "job_id" in data
    assert data["status"] == "queued"


def test_approve_parameters_returns_job_id(monkeypatch):
    from app.core.config import settings
    import os, json

    paper_id = "test_paper_approve"
    json_path = os.path.join(settings.EXTRACTED_JSON_DIR, f"{paper_id}.json")
    os.makedirs(settings.EXTRACTED_JSON_DIR, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"metadata": {"title": "Test Paper"}, "extracted_parameters": {}}, f)

    try:
        resp = client.post(
            f"/api/v1/history/{paper_id}/approve_parameters",
            json={"custom_parameters": {"epochs": 10}}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "job_id" in data
        assert data["status"] == "completed"
        assert data["paper_id"] == paper_id
    finally:
        if os.path.exists(json_path):
            os.remove(json_path)


def test_telemetry_traces_and_alias():
    # 1. Canonical /api/v1/history/{paper_id}/traces
    resp1 = client.get("/api/v1/history/paper_test/traces")
    assert resp1.status_code == 200
    assert "traces" in resp1.json()

    # 2. Alias /api/v1/papers/{paper_id}/execution-traces
    resp2 = client.get("/api/v1/papers/paper_test/execution-traces")
    assert resp2.status_code == 200
    assert "traces" in resp2.json()


def test_paper_task_and_walkthrough_endpoints():
    # 1. /api/v1/history/{paper_id}/task
    t_resp = client.get("/api/v1/history/paper_demo/task")
    assert t_resp.status_code == 200
    assert "content" in t_resp.json()
    assert len(t_resp.json()["content"]) > 0

    # 2. /api/v1/history/{paper_id}/walkthrough
    w_resp = client.get("/api/v1/history/paper_demo/walkthrough")
    assert w_resp.status_code == 200
    assert "content" in w_resp.json()
    assert len(w_resp.json()["content"]) > 0
