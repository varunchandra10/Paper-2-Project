"""
Phase 10: Reproducibility & Run Manifests Test Suite
Verifies:
1. Complete 18-field provenance manifest creation according to Phase 10 spec.
2. Cryptographic SHA-256 input document hashing.
3. System, software, and hardware environment capture.
4. Atomic persistence to storage/manifests/{run_id}.json.
5. Exit criteria fulfillment: reconstructing and explaining previous runs via explain_run().
6. API endpoint integration (/manifest/{run_id} and /manifest/{run_id}/explain).
"""

import os
import json
import pytest
from pathlib import Path
from starlette.testclient import TestClient

from app.core.config import settings
from app.core.manifest import (
    generate_run_manifest,
    save_manifest,
    get_manifest,
    list_manifests,
    explain_run,
    compute_file_sha256,
    RunManifest
)
from main import app

client = TestClient(app)


@pytest.fixture
def temp_manifest_dir(tmp_path, monkeypatch):
    """Provides an isolated directory for run manifests."""
    m_dir = str(tmp_path / "manifests")
    os.makedirs(m_dir, exist_ok=True)
    monkeypatch.setattr(settings, "MANIFESTS_DIR", m_dir)
    return m_dir


def test_manifest_generation_all_18_fields(temp_manifest_dir, tmp_path):
    """
    CRITICAL TEST: Verifies that every single field required by Phase 10 is recorded.
    """
    # Create sample dummy PDF file to hash
    dummy_pdf = tmp_path / "sample_paper.pdf"
    dummy_pdf.write_bytes(b"%PDF-1.5 %Sample research paper content for hash validation.")

    manifest = generate_run_manifest(
        run_id="run_manifest_test_01",
        paper_id="paper_sample_v2",
        pdf_path=str(dummy_pdf),
        model_name="qwen2.5:7b",
        temperature=0.0,
        top_k=5,
        chunk_size=500,
        chunk_overlap=50,
        execution_summary={"status": "VERIFIED", "fidelity_score": 85.0}
    )

    # 1. Top-level identifiers
    assert manifest.run_id == "run_manifest_test_01"
    assert manifest.paper_id == "paper_sample_v2"
    assert "timestamp" in manifest.model_dump()

    # 2. Paper & Hash
    assert manifest.paper.paper_id == "paper_sample_v2"
    assert len(manifest.paper.paper_hash) == 64  # Valid SHA-256 hex string
    assert manifest.paper.paper_version == "1.0.0"
    assert manifest.paper.file_name == "sample_paper.pdf"
    assert manifest.paper.file_size_bytes > 0

    # 3. Model Configuration
    assert manifest.model_info.model == "qwen2.5:7b"
    assert "qwen" in manifest.model_info.model_version
    assert manifest.model_info.provider == "ollama"
    assert manifest.model_info.temperature == 0.0
    assert manifest.model_info.prompt_version == "v2.0.0"

    # 4. Retrieval Configuration
    assert manifest.retrieval_config.embedding_model == "nomic-embed-text"
    assert manifest.retrieval_config.embedding_version == "2.0.0"
    assert manifest.retrieval_config.embedding_dimension == 768
    assert manifest.retrieval_config.chunk_size == 500
    assert manifest.retrieval_config.chunk_overlap == 50
    assert manifest.retrieval_config.top_k == 5
    assert manifest.retrieval_config.retrieval_strategy == "hybrid_rrf"

    # 5. System Configuration
    assert len(manifest.system.os) > 0
    assert len(manifest.system.platform) > 0
    assert len(manifest.system.python_version) > 0
    assert len(manifest.system.torch_version) > 0
    assert manifest.system.software_version == settings.VERSION

    # 6. Hardware Configuration
    assert len(manifest.hardware.cpu) > 0
    assert manifest.hardware.cpu_cores > 0
    assert manifest.hardware.total_ram_gb > 0.0


def test_deterministic_sha256_hashing(tmp_path):
    """Verifies that identical file content generates identical hash, and modifications change hash."""
    file1 = tmp_path / "paper_1.pdf"
    file2 = tmp_path / "paper_2.pdf"
    file3 = tmp_path / "paper_3.pdf"

    content_a = b"Consistent IEEE remote sensing change detection paper bytes."
    content_b = b"Modified remote sensing change detection paper bytes."

    file1.write_bytes(content_a)
    file2.write_bytes(content_a)
    file3.write_bytes(content_b)

    hash1 = compute_file_sha256(str(file1))
    hash2 = compute_file_sha256(str(file2))
    hash3 = compute_file_sha256(str(file3))

    assert hash1 == hash2
    assert hash1 != hash3


def test_atomic_persistence_and_retrieval(temp_manifest_dir):
    """Verifies that generated manifests persist and can be retrieved by run_id."""
    manifest = generate_run_manifest(
        run_id="run_persistence_99",
        paper_id="paper_persistence",
        model_name="qwen2.5:7b"
    )

    loaded = get_manifest("run_persistence_99")
    assert loaded is not None
    assert loaded["run_id"] == "run_persistence_99"
    assert loaded["paper_id"] == "paper_persistence"
    assert loaded["model_config"]["model"] == "qwen2.5:7b"

    manifest_list = list_manifests()
    assert any(m["run_id"] == "run_persistence_99" for m in manifest_list)


def test_exit_criteria_run_explanation(temp_manifest_dir, tmp_path):
    """
    EXIT CRITERIA TEST:
    A previous run can be reconstructed well enough to explain why it produced its result.
    """
    dummy_pdf = tmp_path / "vlcd_reconstruct.pdf"
    dummy_pdf.write_bytes(b"VLCD Research Document")

    manifest = generate_run_manifest(
        run_id="run_vlcd_audit_01",
        paper_id="VLCD_change_detection_2025",
        pdf_path=str(dummy_pdf),
        model_name="qwen2.5:7b",
        temperature=0.0,
        top_k=5,
        execution_summary={
            "field_accuracy": 72.73,
            "hallucinations": 0,
            "code_pass_rate": "100.0%"
        }
    )

    explanation = explain_run("run_vlcd_audit_01")
    assert explanation["reproducible"] is True
    assert explanation["paper_id"] == "VLCD_change_detection_2025"
    assert len(explanation["paper_hash"]) == 64

    # Detailed human-auditable narrative
    narrative = explanation["explanation"]
    assert "Analysis Run 'run_vlcd_audit_01'" in narrative
    assert "VLCD_change_detection_2025" in narrative
    assert "qwen2.5:7b" in narrative
    assert "nomic-embed-text" in narrative
    assert "chunk_size=500" in narrative

    # Reproducibility factors
    factors = explanation["reproducibility_factors"]
    assert factors["deterministic_sampling"] is True
    assert factors["exact_model"] == "qwen2.5:7b"
    assert factors["exact_prompt_version"] == "v2.0.0"


def test_manifest_api_endpoints(temp_manifest_dir):
    """Verifies FastAPI endpoints for manifest retrieval and explanation."""
    generate_run_manifest(
        run_id="run_api_endpoint_test",
        paper_id="paper_api_test",
        model_name="qwen2.5:7b"
    )

    # 1. GET /api/v1/pipeline/manifest/{run_id}
    res_manifest = client.get("/api/v1/pipeline/manifest/run_api_endpoint_test")
    assert res_manifest.status_code == 200
    data = res_manifest.json()
    assert data["run_id"] == "run_api_endpoint_test"
    assert data["paper_id"] == "paper_api_test"

    # 2. GET /api/v1/pipeline/manifest/{run_id}/explain
    res_explain = client.get("/api/v1/pipeline/manifest/run_api_endpoint_test/explain")
    assert res_explain.status_code == 200
    exp_data = res_explain.json()
    assert exp_data["reproducible"] is True
    assert "Analysis Run 'run_api_endpoint_test'" in exp_data["explanation"]

    # 3. GET /api/v1/pipeline/manifests
    res_list = client.get("/api/v1/pipeline/manifests")
    assert res_list.status_code == 200
    items = res_list.json()
    assert any(it["run_id"] == "run_api_endpoint_test" for it in items)

    # 4. 404 on nonexistent manifest
    res_404 = client.get("/api/v1/pipeline/manifest/nonexistent_run_999")
    assert res_404.status_code == 404
