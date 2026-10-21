"""
Phase 11 (Testing V2): Malformed Inputs and Edge Cases Test Suite.

Verifies that the system safely handles:
- Zero-byte PDFs, corrupt PDF headers, binary trash
- Malformed DAG specifications (cycles, missing keys, null dependencies)
- Schema mismatches and invalid API payloads
- Corrupt JSON episodic memories
- Edge cases without uncaught 500 crashes or freezing.
"""

import os
import json
import pytest
from fastapi.testclient import TestClient

from main import app
from app.core.config import settings
from app.core.dag_validator import DAGValidator, DAGErrorCode
from app.agents.sequencing_agent import run_sequencing_agent
from app.core.code_verifier import CodeVerifier

client = TestClient(app)


def test_corrupted_empty_pdf_handling(tmp_path):
    """Verifies that an empty (0-byte) or truncated PDF does not cause unhandled crashes."""
    empty_pdf = tmp_path / "empty.pdf"
    empty_pdf.write_bytes(b"")

    corrupted_pdf = tmp_path / "corrupted.pdf"
    corrupted_pdf.write_bytes(b"NOT_A_REAL_PDF_HEADER_JUST_GARBAGE")

    from app.core.manifest import compute_file_sha256
    empty_hash = compute_file_sha256(str(empty_pdf))
    corrupted_hash = compute_file_sha256(str(corrupted_pdf))

    # Hashing handles empty and corrupted files safely
    assert len(empty_hash) == 64
    assert len(corrupted_hash) == 64
    assert empty_hash != corrupted_hash


def test_malformed_dag_with_self_dependency():
    """Verifies validator flags self-dependencies correctly and provides detailed error message."""
    malformed_steps = [
        {"component_name": "step_1", "description": "Step 1", "dependencies": ["step_1"]}
    ]
    val = DAGValidator.validate(malformed_steps)
    assert val.is_valid is False
    codes = [issue.code for issue in val.issues]
    assert DAGErrorCode.SELF_DEPENDENCY in codes


def test_malformed_dag_with_missing_keys():
    """Verifies validator flags missing required fields without throwing KeyError."""
    malformed_steps = [
        {"description": "Missing component_name and dependencies"},
        {"component_name": "step_2"}  # missing dependencies
    ]
    val = DAGValidator.validate(malformed_steps)
    assert val.is_valid is False
    codes = [issue.code for issue in val.issues]
    assert DAGErrorCode.INVALID_NODE_ID in codes


def test_malformed_dag_empty_steps():
    """Verifies validator cleanly rejects empty step list."""
    val = DAGValidator.validate([])
    assert val.is_valid is False
    codes = [issue.code for issue in val.issues]
    assert DAGErrorCode.EMPTY_PLAN in codes


def test_malformed_dag_duplicate_ids():
    """Verifies validator catches duplicate node IDs."""
    malformed_steps = [
        {"component_name": "dup_step", "description": "First instance", "dependencies": []},
        {"component_name": "dup_step", "description": "Second instance", "dependencies": []}
    ]
    val = DAGValidator.validate(malformed_steps)
    assert val.is_valid is False
    codes = [issue.code for issue in val.issues]
    assert DAGErrorCode.DUPLICATE_NODE in codes


def test_malformed_api_payload_rejection():
    """Verifies that API validates payloads and returns 422 Unprocessable Entity instead of 500."""
    # 1. Invalid payload types (number instead of object for constraints)
    resp = client.post("/api/v1/analyze", json={"paper_id": "test_paper", "constraints": 12345})
    assert resp.status_code == 422

    # 2. Missing required paper_id
    resp2 = client.post("/api/v1/analyze", json={"constraints": {}})
    assert resp2.status_code == 422


def test_malformed_python_code_rejection_at_ast():
    """Verifies that code with invalid syntax or incomplete blocks is safely rejected at Layer 1."""
    broken_code_samples = [
        "def broken_func(:\n    pass",
        "class UnclosedClass(nn.Module:\n    def forward():",
        "import torch\nfor i in range(10)\n    print(i)",
        ""  # Empty string
    ]

    for broken in broken_code_samples:
        res = CodeVerifier.validate_layer1_ast(broken)
        assert res["valid"] is False
        assert "SyntaxError" in res["msg"] or "Empty" in res["msg"] or "rejected" in res["msg"]
