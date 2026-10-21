import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_analyze_and_status_endpoints():
    # 1. Test POST /api/v1/analyze
    resp = client.post("/api/v1/analyze", json={"paper_id": "test_paper_1", "constraints": {"gpu": "rtx"}})
    assert resp.status_code == 200
    data = resp.json()
    assert "job_id" in data
    assert data["job_id"].startswith("job_")
    assert data["status"] == "queued"
    assert data["paper_id"] == "test_paper_1"
    job_id = data["job_id"]

    # 2. Test GET /api/v1/analyze/{job_id}/status
    status_resp = client.get(f"/api/v1/analyze/{job_id}/status")
    assert status_resp.status_code == 200
    s_data = status_resp.json()
    assert s_data["job_id"] == job_id
    assert s_data["paper_id"] == "test_paper_1"
    assert s_data["status"] in ["queued", "running", "completed", "failed"]
    assert "progress" in s_data
    assert isinstance(s_data["progress"], (int, float))

    # 3. Test GET /api/v1/extraction/status/{job_id} (alias)
    alias_resp = client.get(f"/api/v1/extraction/status/{job_id}")
    assert alias_resp.status_code == 200
    assert alias_resp.json()["job_id"] == job_id
    assert alias_resp.json()["paper_id"] == "test_paper_1"


def test_trigger_analysis_legacy_alias():
    resp = client.post("/api/v1/history/test_paper_legacy/trigger_analysis?model_name=gemini-2.5-flash")
    assert resp.status_code == 200
    data = resp.json()
    assert "job_id" in data
    assert data["job_id"].startswith("job_")
    assert data["status"] == "queued"
    assert data["paper_id"] == "test_paper_legacy"


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
            json={"custom_parameters": {"epochs": 10, "optimizer": "AdamW"}}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "job_id" in data
        assert data["status"] == "completed"
        assert data["paper_id"] == paper_id

        # Verify semantic persistence to disk
        with open(json_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        assert saved_data["parameters_approved"] is True
        assert saved_data["extracted_parameters"]["epochs"]["value"] == 10
        assert saved_data["extracted_parameters"]["epochs"]["status"] == "USER_DEFINED"
        assert saved_data["extracted_parameters"]["optimizer"]["value"] == "AdamW"
    finally:
        if os.path.exists(json_path):
            os.remove(json_path)


def test_telemetry_traces_and_alias():
    # 1. Canonical /api/v1/history/{paper_id}/traces
    resp1 = client.get("/api/v1/history/paper_test/traces")
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert "traces" in data1
    assert isinstance(data1["traces"], list)

    # 2. Alias /api/v1/papers/{paper_id}/execution-traces
    resp2 = client.get("/api/v1/papers/paper_test/execution-traces")
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert "traces" in data2
    assert isinstance(data2["traces"], list)


def test_paper_task_and_walkthrough_endpoints():
    # 1. /api/v1/history/{paper_id}/task
    t_resp = client.get("/api/v1/history/paper_demo/task")
    assert t_resp.status_code == 200
    t_data = t_resp.json()
    assert "content" in t_data
    assert len(t_data["content"]) > 0
    assert "# Implementation Task" in t_data["content"] or "Task" in t_data["content"]

    # 2. /api/v1/history/{paper_id}/walkthrough
    w_resp = client.get("/api/v1/history/paper_demo/walkthrough")
    assert w_resp.status_code == 200
    w_data = w_resp.json()
    assert "content" in w_data
    assert len(w_data["content"]) > 0
    assert "# Walkthrough" in w_data["content"] or "Walkthrough" in w_data["content"]

