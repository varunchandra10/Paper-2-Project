import sys
import os
import pytest
from fastapi.testclient import TestClient

# Add new_backend to python search path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from main import app

client = TestClient(app)


def test_root_status():
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "online"


def test_list_papers():
    resp = client.get("/papers")
    assert resp.status_code == 200
    data = resp.json()
    assert "papers" in data


def test_auth_flow():
    # Register
    reg_resp = client.post("/auth/register", json={
        "email": "step7_test@example.com",
        "password": "testpassword123",
        "full_name": "Step 7 Tester"
    })
    assert reg_resp.status_code in [200, 400]

    # Login
    login_resp = client.post("/auth/login", json={
        "email": "step7_test@example.com",
        "password": "testpassword123"
    })
    assert login_resp.status_code == 200
    assert "user" in login_resp.json()


def test_telemetry_and_evals_endpoints():
    traces_resp = client.get("/history/paper_2/traces")
    assert traces_resp.status_code == 200
    assert "traces" in traces_resp.json()

    eval_resp = client.get("/evals/benchmark/paper_2")
    assert eval_resp.status_code == 200
    assert "reliability_score" in eval_resp.json()


def test_chat_endpoint():
    chat_resp = client.post("/conversations/conv_step7/chat", json={
        "message": "Hello Synthexis 2.0"
    })
    assert chat_resp.status_code == 200
    data = chat_resp.json()
    assert "content" in data


if __name__ == "__main__":
    print("Running Step 7 API Endpoints & Server Entrypoint tests...")
    test_root_status()
    test_list_papers()
    test_auth_flow()
    test_telemetry_and_evals_endpoints()
    test_chat_endpoint()
    print("All Step 7 API Endpoints tests passed successfully!")
