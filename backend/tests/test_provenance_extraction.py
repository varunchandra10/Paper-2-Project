"""
Verification tests for Phase 3: Provenance-Aware Extraction.
Verifies that parameters distinguish EXPLICIT facts from inferences/defaults,
track verbatim text evidence and section coordinates, honestly represent absent
fields as UNKNOWN, and never silently fabricate hardcoded defaults.
"""

import json
import pytest
from unittest.mock import patch, MagicMock

from app.schemas.pipeline import ExtractedParameters, ParameterDetails, ProvenanceStatus
from app.schemas.pipeline_schemas import ProjectParameter
from app.agents.parameter_agent import run_parameter_agent
from app.core.code_verifier import CodeVerifier


def test_explicit_parameter_with_verbatim_evidence():
    """
    Verify that explicit parameters are captured with verbatim evidence,
    correct section coordinates, and STRONG evidence strength.
    """
    mock_llm_output = {
        "parameters": {
            "learning_rate": {
                "value": "0.0002",
                "status": "EXPLICIT",
                "evidence": "We set the initial learning rate to 2e-4 using the AdamW optimizer.",
                "source_section": "Section 4.1 Training Details",
                "evidence_strength": "STRONG",
                "rationale": "Explicitly stated in Section 4.1"
            },
            "optimizer": {
                "value": "AdamW",
                "status": "EXPLICIT",
                "evidence": "All models were optimized using AdamW with beta1=0.9 and beta2=0.999.",
                "source_section": "Section 4.1",
                "evidence_strength": "STRONG"
            }
        }
    }

    with patch("app.agents.parameter_agent.ModelRouter") as mock_router_cls:
        mock_router = MagicMock()
        mock_router.generate.return_value = (json.dumps(mock_llm_output), {})
        mock_router_cls.return_value = mock_router

        res = run_parameter_agent(raw_text="Sample text")

        # Verify learning_rate provenance
        lr = res.learning_rate
        assert lr.value == "0.0002"
        assert lr.status == ProvenanceStatus.EXPLICIT.value
        assert "initial learning rate to 2e-4" in lr.evidence
        assert lr.source_section == "Section 4.1 Training Details"
        assert lr.evidence_strength == "STRONG"
        assert lr.is_known is True

        # Verify optimizer provenance
        opt = res.optimizer
        assert opt.value == "AdamW"
        assert opt.status == ProvenanceStatus.EXPLICIT.value
        assert "AdamW" in opt.evidence


def test_absent_parameter_honest_unknown():
    """
    Verify that parameters absent from the paper are honestly marked as UNKNOWN,
    with None value, None evidence, and NONE evidence strength.
    """
    mock_llm_output = {
        "parameters": {
            "learning_rate": {
                "value": "0.001",
                "status": "EXPLICIT",
                "evidence": "learning rate of 0.001"
            }
            # batch_size, epochs, backbone are NOT mentioned
        }
    }

    with patch("app.agents.parameter_agent.ModelRouter") as mock_router_cls:
        mock_router = MagicMock()
        mock_router.generate.return_value = (json.dumps(mock_llm_output), {})
        mock_router_cls.return_value = mock_router

        res = run_parameter_agent(raw_text="Sample text")

        # batch_size was not in paper -> must be UNKNOWN
        bs = res.batch_size
        assert bs.value is None
        assert bs.status == ProvenanceStatus.UNKNOWN.value
        assert bs.evidence is None
        assert bs.evidence_strength == "NONE"
        assert bs.is_known is False

        # epochs was not in paper -> must be UNKNOWN
        ep = res.epochs
        assert ep.value is None
        assert ep.status == ProvenanceStatus.UNKNOWN.value
        assert ep.is_known is False


def test_derived_parameter_provenance():
    """
    Verify that derived parameters track computation rationale.
    """
    mock_llm_output = {
        "parameters": {
            "effective_batch_size": {
                "value": "128",
                "status": "DERIVED",
                "rationale": "Computed as 16 images/gpu * 8 A100 GPUs",
                "evidence_strength": "STRONG"
            }
        }
    }

    with patch("app.agents.parameter_agent.ModelRouter") as mock_router_cls:
        mock_router = MagicMock()
        mock_router.generate.return_value = (json.dumps(mock_llm_output), {})
        mock_router_cls.return_value = mock_router

        res = run_parameter_agent(raw_text="Sample text")
        ebs = res.custom_parameters.get("effective_batch_size")
        assert ebs is not None
        assert ebs.value == "128"
        assert ebs.status == ProvenanceStatus.DERIVED.value
        assert "16 images/gpu * 8" in ebs.rationale


def test_anti_hallucination_explicit_without_evidence_downgraded():
    """
    Verify that if the LLM marks a parameter as EXPLICIT but provides no evidence quote,
    the system downgrades the status to INFERRED to protect factual integrity.
    """
    mock_llm_output = {
        "parameters": {
            "warmup_epochs": {
                "value": "5",
                "status": "EXPLICIT",
                "evidence": None  # No verbatim quote provided!
            }
        }
    }

    with patch("app.agents.parameter_agent.ModelRouter") as mock_router_cls:
        mock_router = MagicMock()
        mock_router.generate.return_value = (json.dumps(mock_llm_output), {})
        mock_router_cls.return_value = mock_router

        res = run_parameter_agent(raw_text="Sample text")
        wp = res.custom_parameters["warmup_epochs"]
        assert wp.status == ProvenanceStatus.INFERRED.value, "Must downgrade unevidenced EXPLICIT claim"
        assert wp.evidence_strength == "MODERATE"


def test_no_silent_fallback_fabrication_on_error():
    """
    Verify that when parameter extraction encounters an error, it returns
    clean UNKNOWN states rather than fabricated defaults (0.0001, AdamW, Swin-T).
    """
    with patch("app.agents.parameter_agent.ModelRouter") as mock_router_cls:
        mock_router = MagicMock()
        mock_router.generate.side_effect = RuntimeError("LLM API failure")
        mock_router_cls.return_value = mock_router

        res = run_parameter_agent(raw_text="Text")

        assert res.learning_rate.value is None
        assert res.learning_rate.status == ProvenanceStatus.UNKNOWN.value
        assert res.batch_size.value is None
        assert res.batch_size.status == ProvenanceStatus.UNKNOWN.value
        assert res.optimizer.value is None
        assert res.backbone.value is None


def test_extracted_parameters_get_effective_value():
    """
    Verify get_effective_value distinguishes known facts from assumed defaults.
    """
    params = ExtractedParameters(
        learning_rate=ParameterDetails(value="0.0003", status="EXPLICIT", evidence="lr=3e-4"),
        batch_size=ParameterDetails(status="UNKNOWN")
    )

    # Known parameter
    val, status = params.get_effective_value("learning_rate", fallback_default="0.001")
    assert val == "0.0003"
    assert status == "EXPLICIT"

    # Unknown parameter -> returns fallback with ASSUMED_DEFAULT status
    val_bs, status_bs = params.get_effective_value("batch_size", fallback_default="16")
    assert val_bs == "16"
    assert status_bs == "ASSUMED_DEFAULT"


def test_code_verifier_ignores_unknown_parameters():
    """
    Verify that CodeVerifier Layer 2 grounding ignores UNKNOWN parameters
    and does not unfairly penalize code for omitting unspecified values.
    """
    code = """
import torch
import torch.nn as nn

class ResNetBackbone(nn.Module):
    def __init__(self, in_channels=3, num_classes=10):
        super().__init__()
        self.fc = nn.Linear(512, num_classes)

    def forward(self, x):
        return self.fc(x)
"""
    # Parameters with one explicit (num_classes=10) and several UNKNOWNs
    test_params = {
        "num_classes": "10",
        "learning_rate": None,
        "warmup_epochs": "Not specified",
        "weight_decay": "UNKNOWN"
    }

    grounding = CodeVerifier.calculate_layer2_grounding(code, parameters=test_params)
    assert grounding["param_score"] > 0.0
    # "num_classes=10" should match
    assert any("num_classes=10" in m for m in grounding["param_matches"])
    # UNKNOWN parameters should NOT be in misses
    assert not any("learning_rate" in m for m in grounding["param_misses"])
    assert not any("warmup_epochs" in m for m in grounding["param_misses"])
