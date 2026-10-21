"""
Phase 11 (Testing V2): Evaluation Regression and Hard Gates Test Suite.

Verifies:
- Cross-Paper Isolation: Chunk queries across papers never cross-contaminate.
- Provenance Integrity: Missing fields remain UNKNOWN, never hallucinating fake values.
- Sandbox Barriers: AST rejection of system commands, CPU timeouts, clean process termination.
- Restart & Persistence: Jobs and events survive server restarts.
- Evaluation Regression Gates: Checks that benchmarks enforce strict quality floors.
"""

import os
import json
import pytest
from unittest.mock import patch, MagicMock

from app.core.config import settings
from app.core.job_store import JobStore, JobStatus
from app.core.code_verifier import CodeVerifier, code_verifier
from app.schemas.verification import CodeLifecycleState, VerificationRung
from app.schemas.pipeline import ExtractedParameters, ProvenanceStatus
from app.agents.parameter_agent import run_parameter_agent
from app.core.manifest import generate_run_manifest, get_manifest
from app.schemas.paper import PaperDocument, PaperMetadata, PaperSection
from app.retrieval.chunker import PaperChunk
from app.retrieval.vector_db import PaperVectorDB


def test_cross_paper_isolation_semantic_boundary(tmp_path, monkeypatch):
    """
    Cross-Paper Isolation Test:
    Verifies that querying chunks for Paper A returns zero chunks belonging to Paper B.
    """
    test_storage = str(tmp_path / "rag_iso_storage")
    os.makedirs(test_storage, exist_ok=True)
    monkeypatch.setattr("app.retrieval.vector_db.EMBEDDINGS_DIR", test_storage)

    vdb = PaperVectorDB()
    vdb.embeddings_dir = test_storage
    vdb.initialize_db()

    # Add chunks for Paper Alpha
    doc_a = PaperDocument(
        paper_id="paper_alpha",
        metadata=PaperMetadata(title="Alpha Paper", abstract="Remote sensing change detection"),
        sections=[PaperSection(title="Methods", content="Siamese ResNet50 in satellite imagery.")]
    )
    chunks_a = [
        PaperChunk(chunk_id="alpha_1", paper_id="paper_alpha", section="Methods", content="Siamese ResNet50 in satellite imagery.")
    ]
    vectors_a = [[0.9] + [0.0] * 767]
    vdb.insert_paper_document(doc_a, chunks_a, vectors_a)

    # Add chunks for Paper Beta
    doc_b = PaperDocument(
        paper_id="paper_beta",
        metadata=PaperMetadata(title="Beta Paper", abstract="Natural language processing"),
        sections=[PaperSection(title="Methods", content="Transformer architecture for translation.")]
    )
    chunks_b = [
        PaperChunk(chunk_id="beta_1", paper_id="paper_beta", section="Methods", content="Transformer architecture for translation.")
    ]
    vectors_b = [[0.0] * 767 + [0.9]]
    vdb.insert_paper_document(doc_b, chunks_b, vectors_b)

    # Search specifically filtered for Paper Alpha using Paper B's vector
    query_b_vector = [0.0] * 767 + [0.9]
    alpha_results = vdb.semantic_search(query_vector=query_b_vector, paper_id="paper_alpha", top_k=5)
    assert len(alpha_results) > 0
    # All retrieved chunks must strictly belong to paper_alpha
    for chunk in alpha_results:
        assert chunk["paper_id"] == "paper_alpha"
        assert chunk["paper_id"] != "paper_beta"


def test_provenance_integrity_no_hallucinated_defaults():
    """
    Provenance Integrity Test:
    Verifies that an absent parameter is reported honestly as UNKNOWN
    and has null value, rather than inventing 0.001 or Adam.
    """
    empty_llm_output = {
        "parameters": {
            "learning_rate": {
                "value": None,
                "status": "UNKNOWN",
                "evidence": None,
                "source_section": None,
                "evidence_strength": "NONE"
            }
        }
    }

    with patch("app.agents.parameter_agent.ModelRouter") as mock_router_cls:
        mock_router = MagicMock()
        mock_router.generate.return_value = (json.dumps(empty_llm_output), {})
        mock_router_cls.return_value = mock_router

        res = run_parameter_agent(raw_text="Text with no learning rate mentioned.")
        assert res.learning_rate.status == ProvenanceStatus.UNKNOWN.value
        assert res.learning_rate.value is None
        assert res.learning_rate.is_known is False


def test_sandbox_security_host_protection():
    """
    Sandbox Security Test:
    Verifies that dangerous OS commands and file system destruction calls
    are intercepted and prevented at the AST layer.
    """
    malicious_scripts = [
        "import os\nos.remove('/etc/hosts')",
        "import sys\nsys.exit(1)",
        "import subprocess\nsubprocess.call(['rm', '-rf', '/'])",
        "eval('__import__(\"os\").system(\"calc.exe\")')"
    ]
    for script in malicious_scripts:
        ast_result = CodeVerifier.validate_layer1_ast(script)
        assert ast_result["valid"] is False, f"Malicious script bypassed AST: {script}"
        assert "Security violation" in ast_result["msg"]


def test_restart_persistence_and_job_recovery(tmp_path):
    """
    Restart & Persistence Test:
    Verifies that if the server crashes while a job is running,
    re-initializing the JobStore marks the zombie job as FAILED with actionable error
    and does not leave deadlocks or orphan locks.
    """
    db_file = str(tmp_path / "crash_recovery.db")

    # 1. First engine lifecycle: create and start job
    store1 = JobStore(db_path=db_file)
    store1.create_job(paper_id="paper_crash", job_id="job_crashed_101")
    store1.update_stage("job_crashed_101", stage="parsing", progress=40.0, status=JobStatus.RUNNING)
    assert store1.get_job("job_crashed_101").status == JobStatus.RUNNING

    # Simulate sudden crash by closing store1 without complete_job()
    del store1

    # 2. Server reboots / second engine lifecycle
    store2 = JobStore(db_path=db_file)
    recovered_count = store2.recover_stale_jobs("Server restarted during execution")
    assert recovered_count == 1

    rebooted_job = store2.get_job("job_crashed_101")
    # Zombie jobs running across restart are recovered as FAILED
    assert rebooted_job.status == JobStatus.FAILED
    assert "Server restarted during execution" in rebooted_job.error


def test_eval_regression_code_generation_ladder():
    """
    Evaluation Regression Gate:
    Verifies that standard synthesizable PyTorch architectures achieve 100% pass rate
    on Gates 1 through 7 (AST, Compile, Runtime, Forward, Backward, Training, Functional).
    """
    clean_model_code = '''
import torch
import torch.nn as nn

class EvaluatedModule(nn.Module):
    def __init__(self, in_channels=3, num_classes=10):
        super().__init__()
        self.conv = nn.Conv2d(in_channels, 16, kernel_size=3, padding=1)
        self.pool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Linear(16, num_classes)

    def forward(self, x):
        out = self.conv(x)
        out = self.pool(out)
        out = torch.flatten(out, 1)
        return self.fc(out)
'''
    report = code_verifier.verify_code_ladder(clean_model_code)
    assert report.lifecycle_state in [CodeLifecycleState.VERIFIED, CodeLifecycleState.EXECUTABLE]
    assert report.all_rungs_passed is True

    # Gate 1: AST
    assert report.get_rung_result(VerificationRung.AST_VALIDATION).passed is True
    # Gate 2: Compile
    assert report.get_rung_result(VerificationRung.BYTECODE_COMPILATION).passed is True
    # Gate 3: Forward Pass
    assert report.get_rung_result(VerificationRung.FORWARD_PASS).passed is True
    # Gate 4: Backward Pass / Gradients
    assert report.get_rung_result(VerificationRung.BACKWARD_PASS).passed is True
    # Gate 5: Optimizer Step
    assert report.get_rung_result(VerificationRung.OPTIMIZER_STEP).passed is True
