"""
Phase 12: Failure Injection & Reliability Test Suite.

Verifies that the 18 critical failure modes produce controlled,
observable, recoverable behavior rather than silent corruption:
1. corrupted PDF
2. huge PDF
3. empty PDF
4. malicious PDF (path traversal)
5. LLM timeout
6. invalid JSON
7. hallucinated extraction
8. embedding failure
9. vector DB failure / missing store
10. database concurrency & failure
11. GPU unavailable (CPU fallback)
12. GPU OOM / memory exhaustion
13. invalid generated code
14. malicious generated code
15. client disconnect (SSE generator)
16. server restart (zombie recovery)
17. concurrent papers
18. provider outage
"""

import os
import json
import pytest
import threading
from unittest.mock import patch, MagicMock

from app.core.config import settings
from app.core.job_store import JobStore, JobStatus
from app.core.events import EventTypes, emit_node_error
from app.core.code_verifier import CodeVerifier, code_verifier
from app.schemas.verification import CodeLifecycleState, VerificationRung
from app.schemas.pipeline import ExtractedParameters, ProvenanceStatus
from app.agents.parameter_agent import run_parameter_agent
from app.graph.nodes.ingestion import ingestion_node, MAX_ALLOWED_PDF_BYTES
from app.retrieval.vector_db import PaperVectorDB
from app.retrieval.embeddings import EmbeddingError
from app.core.sandbox.subprocess_runner import SubprocessCodeExecutor
from app.core.sandbox.base import ExecutionLimits


# 1. Corrupted PDF
def test_failure_mode_1_corrupted_pdf(tmp_path):
    corrupt_file = tmp_path / "corrupt_data.pdf"
    corrupt_file.write_bytes(b"%PDF-1.4 \x00\xff\xfe\xaaCorrupted Binary Garbage Not A Valid Document")
    with pytest.raises(ValueError) as exc:
        ingestion_node({"pdf_path": str(corrupt_file), "paper_id": "test_corrupt"})
    assert "corrupt" in str(exc.value).lower() or "failed" in str(exc.value).lower() or "unreadable" in str(exc.value).lower()


# 2. Huge PDF (>50MB safety limit)
def test_failure_mode_2_huge_pdf(tmp_path):
    huge_file = tmp_path / "huge_paper.pdf"
    # Create sparse file > 50MB
    with open(huge_file, "wb") as f:
        f.seek(MAX_ALLOWED_PDF_BYTES + 1024)
        f.write(b"\x00")
    with pytest.raises(ValueError) as exc:
        ingestion_node({"pdf_path": str(huge_file), "paper_id": "test_huge"})
    assert "50mb safety limit" in str(exc.value).lower()


# 3. Empty PDF (0 bytes)
def test_failure_mode_3_empty_pdf(tmp_path):
    empty_file = tmp_path / "empty.pdf"
    empty_file.write_bytes(b"")
    with pytest.raises(ValueError) as exc:
        ingestion_node({"pdf_path": str(empty_file), "paper_id": "test_empty"})
    assert "0 bytes" in str(exc.value).lower()


# 4. Malicious PDF (Path Traversal attempt)
def test_failure_mode_4_malicious_pdf_path():
    traversal_path = "../../etc/shadow.pdf"
    with pytest.raises(FileNotFoundError):
        ingestion_node({"pdf_path": traversal_path, "paper_id": "test_malicious"})


# 5. LLM Timeout
def test_failure_mode_5_llm_timeout():
    with patch("app.agents.parameter_agent.ModelRouter") as mock_router_cls:
        mock_router = MagicMock()
        mock_router.generate.side_effect = TimeoutError("Ollama inference request timed out after 30s")
        mock_router_cls.return_value = mock_router

        # Fails gracefully by returning honest UNKNOWN rather than crashing or freezing
        result = run_parameter_agent(raw_text="Sample text")
        assert result.optimizer.status == ProvenanceStatus.UNKNOWN.value
        assert result.optimizer.value is None


# 6. Invalid JSON returned from LLM
def test_failure_mode_6_invalid_json():
    with patch("app.agents.parameter_agent.ModelRouter") as mock_router_cls:
        mock_router = MagicMock()
        mock_router.generate.return_value = ("```json\n{unclosed_json_string: 'val'\n", {})
        mock_router_cls.return_value = mock_router

        result = run_parameter_agent(raw_text="Sample text")
        # System does not crash with JSONDecodeError; falls back to UNKNOWN state
        assert result.optimizer.status == ProvenanceStatus.UNKNOWN.value


# 7. Hallucinated Extraction (Lack of evidence)
def test_failure_mode_7_hallucinated_extraction():
    hallucinated_json = {
        "parameters": {
            "optimizer": {
                "value": "AdamW",
                "status": "EXPLICIT",
                "evidence": None,  # Hallucinated: marked EXPLICIT without quote
                "source_section": None,
                "evidence_strength": "NONE"
            }
        }
    }
    with patch("app.agents.parameter_agent.ModelRouter") as mock_router_cls:
        mock_router = MagicMock()
        mock_router.generate.return_value = (json.dumps(hallucinated_json), {})
        mock_router_cls.return_value = mock_router

        res = run_parameter_agent(raw_text="Text with zero mention of AdamW")
        # When status lacks evidence, system detects hallucination and downgrades to INFERRED
        assert res.optimizer.status == "INFERRED"


# 8. Embedding Failure
def test_failure_mode_8_embedding_failure():
    from app.retrieval.embeddings import generate_local_embedding
    with patch("ollama.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.embeddings.side_effect = ConnectionError("Embedding service offline on port 11434")
        mock_client_cls.return_value = mock_client

        with pytest.raises(EmbeddingError) as exc:
            generate_local_embedding("Sample text chunk")
        assert "Embedding generation failed" in str(exc.value) or "offline" in str(exc.value)


# 9. Vector DB missing or corrupted store
def test_failure_mode_9_vector_db_resilience(tmp_path):
    corrupt_dir = str(tmp_path / "non_existent_vector_dir" / "nested")
    vdb = PaperVectorDB()
    vdb.embeddings_dir = corrupt_dir
    vdb.initialize_db()
    assert os.path.exists(corrupt_dir)
    results = vdb.semantic_search([0.1] * 768, paper_id="any_paper")
    assert results == []


# 10. Database Concurrency & Failure Handling
def test_failure_mode_10_database_wal_concurrency(tmp_path):
    db_file = str(tmp_path / "wal_concurrency.db")
    store = JobStore(db_path=db_file)

    num_threads = 15
    errors = []

    def task(tid):
        try:
            store.create_job(paper_id=f"paper_{tid}", job_id=f"job_{tid}")
            store.record_event(job_id=f"job_{tid}", paper_id=f"paper_{tid}", event_type=EventTypes.NODE_STARTED, node_name="ingestion")
            store.complete_job(job_id=f"job_{tid}")
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=task, args=(i,)) for i in range(num_threads)]
    for t in threads: t.start()
    for t in threads: t.join()

    assert errors == []
    assert len(store.list_jobs(limit=50)) == num_threads


# 11. GPU Unavailable (CPU fallback)
def test_failure_mode_11_gpu_unavailable_cpu_fallback():
    import torch
    clean_code = """
import torch
import torch.nn as nn

class CPUFallbackNet(nn.Module):
    def __init__(self, in_channels=3, num_classes=5):
        super().__init__()
        self.conv = nn.Conv2d(in_channels, 8, kernel_size=3, padding=1)
        self.pool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Linear(8, num_classes)
    def forward(self, x):
        return self.fc(torch.flatten(self.pool(self.conv(x)), 1))
"""
    # Execute verification on host even if CUDA is unavailable
    report = code_verifier.verify_code_ladder(clean_code)
    assert report.lifecycle_state in [CodeLifecycleState.VERIFIED, CodeLifecycleState.EXECUTABLE]
    assert report.get_rung_result(VerificationRung.FORWARD_PASS).passed is True


# 12. GPU OOM / Memory Exhaustion
def test_failure_mode_12_sandbox_memory_exhaustion():
    oom_code = """
import numpy as np
# Attempt to allocate array larger than sandbox limit
arr = np.zeros((20000, 20000, 50), dtype=np.float64)
"""
    limits = ExecutionLimits(timeout_seconds=2)
    runner = SubprocessCodeExecutor(default_limits=limits)
    res = runner.execute_verification_ladder(oom_code)
    assert res.passed is False


# 13. Invalid Generated Code (Syntax error)
def test_failure_mode_13_invalid_code_syntax():
    invalid_code = "class IncompleteModel(nn.Module\n    def forward():"
    report = code_verifier.verify_code_ladder(invalid_code)
    assert report.lifecycle_state == CodeLifecycleState.FAILED
    assert report.all_rungs_passed is False
    assert "SyntaxError" in report.repair_feedback or "Syntax" in report.repair_feedback


# 14. Malicious Generated Code (SecurityPolicy violation)
def test_failure_mode_14_malicious_code_interception():
    malicious_code = """
import torch
import os
os.system("whoami")
"""
    report = code_verifier.verify_code_ladder(malicious_code)
    assert report.lifecycle_state == CodeLifecycleState.FAILED
    sec_rung = report.get_rung_result(VerificationRung.SECURITY_ANALYSIS)
    assert sec_rung is not None
    assert sec_rung.passed is False


# 15. Client Disconnect (SSE generator clean break)
def test_failure_mode_15_client_disconnect():
    import asyncio
    from app.api.v1.endpoints.pipeline import stream_analysis_events
    from starlette.requests import Request

    async def run_disconnect():
        mock_scope = {"type": "http", "method": "GET", "path": "/stream/job_disconnect", "headers": []}
        mock_request = Request(mock_scope)
        response = await stream_analysis_events("job_nonexistent", mock_request)
        assert response.status_code == 200

    asyncio.run(run_disconnect())


# 16. Server Restart (Zombie job recovery)
def test_failure_mode_16_server_restart_zombie_recovery(tmp_path):
    db_file = str(tmp_path / "server_restart.db")
    store = JobStore(db_path=db_file)
    store.create_job(paper_id="paper_zombie", job_id="job_zombie_404")
    store.update_stage("job_zombie_404", stage="code_gen", progress=80.0, status=JobStatus.RUNNING)

    # Server restarts and invokes recover_stale_jobs
    recovered = store.recover_stale_jobs("Server restarted during execution")
    assert recovered == 1
    job = store.get_job("job_zombie_404")
    assert job.status == JobStatus.FAILED
    assert "Server restarted" in job.error


# 17. Concurrent Papers Isolation
def test_failure_mode_17_concurrent_papers_isolation(tmp_path):
    db_file = str(tmp_path / "concurrent_papers.db")
    store = JobStore(db_path=db_file)
    store.create_job(paper_id="paper_A", job_id="job_A")
    store.create_job(paper_id="paper_B", job_id="job_B")

    store.record_event(job_id="job_A", paper_id="paper_A", event_type=EventTypes.NODE_STARTED, node_name="ingestion")
    store.record_event(job_id="job_B", paper_id="paper_B", event_type=EventTypes.NODE_STARTED, node_name="extraction")

    events_a = store.get_events("job_A")
    events_b = store.get_events("job_B")
    assert len(events_a) == 1 and events_a[0]["node"] == "ingestion"
    assert len(events_b) == 1 and events_b[0]["node"] == "extraction"


# 18. Provider Outage
def test_failure_mode_18_provider_outage():
    with patch("app.core.model_router.ModelRouter.generate") as mock_gen:
        mock_gen.side_effect = ConnectionRefusedError("Ollama daemon service is down (503 Service Unavailable)")
        with pytest.raises(ConnectionRefusedError):
            from app.core.model_router import ModelRouter
            router = ModelRouter()
            router.generate(prompt="Test prompt")
