"""
Phase 11 (Testing V2): Semantic Assertions & Real Data Flows Test Suite.

Shifts testing from superficial status checks ("assert status_code == 200")
toward deep semantic correctness:
- Parameter extraction statuses (EXPLICIT vs INFERRED vs UNKNOWN)
- Verbatim citation and section coordinates
- Execution plan DAG invariants and topological order
- Verification ladder pass depths
- Manifest cryptographic integrity
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from main import app
from app.core.config import settings
from app.schemas.pipeline import ExtractedParameters, ParameterDetails, ProvenanceStatus
from app.agents.parameter_agent import run_parameter_agent
from app.core.code_verifier import CodeVerifier, code_verifier
from app.schemas.verification import CodeLifecycleState, VerificationRung
from app.core.dag_validator import DAGValidator
from app.core.manifest import generate_run_manifest, compute_file_sha256

client = TestClient(app)


def test_semantic_parameter_extraction_provenance():
    """
    Semantic test: Asserts that extracted parameters contain exact verbatim evidence,
    correct semantic enum status, and honest UNKNOWN classification without synthetic defaults.
    """
    mock_llm_response = {
        "parameters": {
            "optimizer": {
                "value": "AdamW",
                "status": "EXPLICIT",
                "evidence": "We optimize all models using AdamW with weight decay 0.01.",
                "source_section": "Section 4.2 Optimization",
                "evidence_strength": "STRONG",
                "rationale": "Explicitly stated in Section 4.2"
            },
            "learning_rate": {
                "value": "0.0001",
                "status": "EXPLICIT",
                "evidence": "Initial learning rate is set to 1e-4.",
                "source_section": "Section 4.2",
                "evidence_strength": "STRONG",
                "rationale": "Directly specified in text"
            },
            "weight_decay": {
                "value": "0.01",
                "status": "INFERRED",
                "evidence": "Using default AdamW regularization",
                "source_section": "Section 4.2",
                "evidence_strength": "MODERATE",
                "rationale": "Deduced from standard optimizer settings"
            },
            "dropout_rate": {
                "value": None,
                "status": "UNKNOWN",
                "evidence": None,
                "source_section": None,
                "evidence_strength": "NONE",
                "rationale": "Not mentioned in the paper text"
            }
        }
    }

    with patch("app.agents.parameter_agent.ModelRouter") as mock_router_cls:
        mock_router = MagicMock()
        mock_router.generate.return_value = (json.dumps(mock_llm_response), {})
        mock_router_cls.return_value = mock_router

        result = run_parameter_agent(raw_text="Dummy text about AdamW and 1e-4 lr")

        # Semantic Assertions on standard fields
        assert result.optimizer.status == ProvenanceStatus.EXPLICIT.value
        assert result.optimizer.value == "AdamW"
        assert result.optimizer.source_section == "Section 4.2 Optimization"
        assert "weight decay 0.01" in result.optimizer.evidence
        assert result.optimizer.is_known is True

        assert result.learning_rate.status == ProvenanceStatus.EXPLICIT.value
        assert float(result.learning_rate.value) == 0.0001
        assert result.learning_rate.evidence_strength == "STRONG"

        # Semantic Assertions on custom parameters
        wd = result.custom_parameters["weight_decay"]
        assert wd.status == ProvenanceStatus.INFERRED.value
        assert wd.evidence_strength == "MODERATE"
        assert wd.value == "0.01"

        # Honest UNKNOWN verification - no fabricated default
        dr = result.custom_parameters["dropout_rate"]
        assert dr.status == ProvenanceStatus.UNKNOWN.value
        assert dr.value is None
        assert dr.is_known is False


def test_semantic_execution_plan_dag_invariants():
    """
    Semantic test: Verifies topological order, absence of cycles,
    and valid sequential dependencies across execution plan steps.
    """
    steps = [
        {"component_name": "step_1", "description": "Load Dataset", "dependencies": []},
        {"component_name": "step_2", "description": "Extract Features", "dependencies": ["step_1"]},
        {"component_name": "step_3", "description": "Train Backbone", "dependencies": ["step_2"]},
        {"component_name": "step_4", "description": "Evaluate Metrics", "dependencies": ["step_3"]}
    ]

    validation = DAGValidator.validate(steps)
    assert validation.is_valid is True
    assert validation.cycle_path is None
    assert len(validation.issues) == 0

    # Semantic order assertion
    expected_order = ["step_1", "step_2", "step_3", "step_4"]
    assert validation.execution_order == expected_order

    # Verify that each node appears strictly AFTER all of its dependencies
    seen = set()
    for node_id in validation.execution_order:
        node_step = next(s for s in steps if s["component_name"] == node_id)
        for dep in node_step["dependencies"]:
            assert dep in seen, f"Node {node_id} executed before dependency {dep}"
        seen.add(node_id)


def test_semantic_verification_ladder_layers():
    """
    Semantic test: Verifies that code verification outputs are structurally typed,
    validating AST syntax, forbidden operations, compile correctness, and runtime shapes.
    """
    valid_torch_code = '''
import torch
import torch.nn as nn

class TinyClassifier(nn.Module):
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

def create_model():
    return TinyClassifier()
'''

    # Layer 1: AST Semantic Validation
    l1 = CodeVerifier.validate_layer1_ast(valid_torch_code)
    assert l1["valid"] is True
    assert l1["msg"] == "Syntax OK"
    assert l1["is_stub"] is False

    # Layer 2: Bytecode Compilation
    comp = CodeVerifier.validate_bytecode_compilation(valid_torch_code)
    assert comp["valid"] is True

    # Full Ladder
    report = code_verifier.verify_code_ladder(valid_torch_code)
    assert report.lifecycle_state in [CodeLifecycleState.VERIFIED, CodeLifecycleState.EXECUTABLE]
    fwd = report.get_rung_result(VerificationRung.FORWARD_PASS)
    assert fwd is not None
    assert fwd.passed is True


def test_semantic_run_manifest_cryptographic_integrity(tmp_path):
    """
    Semantic test: Asserts that run manifest binds exact SHA-256 paper digest,
    real hardware configurations, and reproduction parameters.
    """
    test_pdf = tmp_path / "semantic_audit_paper.pdf"
    content = b"%PDF-1.4 Mock Remote Sensing Change Detection IEEE Content"
    test_pdf.write_bytes(content)

    expected_hash = compute_file_sha256(str(test_pdf))

    manifest = generate_run_manifest(
        run_id="run_semantic_audit_42",
        paper_id="paper_audit_42",
        pdf_path=str(test_pdf),
        model_name="qwen2.5:7b",
        temperature=0.0,
        top_k=5,
        execution_summary={
            "status": "COMPLETED",
            "verified_gates": 8
        }
    )

    # Semantic integrity assertions
    assert manifest.paper.paper_hash == expected_hash
    assert manifest.paper.file_size_bytes == len(content)
    assert manifest.model_info.model == "qwen2.5:7b"
    assert manifest.model_info.temperature == 0.0
    assert manifest.retrieval_config.top_k == 5
    assert manifest.hardware.cpu_cores > 0
    assert manifest.hardware.total_ram_gb > 0.0
    assert manifest.execution_summary["verified_gates"] == 8
