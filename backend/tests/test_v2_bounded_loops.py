"""
Phase 11 (Testing V2): Bounded Loops and Termination Guarantees Test Suite.

Verifies:
- All iterative agent loops have strict, finite upper bounds (e.g. max_repair_retries <= 2).
- Broken or adversarial outputs never cause infinite loops, runaway recursion, or thread starvation.
- Deterministic fallbacks engage automatically when loop budgets are exhausted.
"""

import pytest
from unittest.mock import patch, MagicMock

from app.core.dag_validator import DAGValidator
from app.agents.sequencing_agent import run_sequencing_agent
from app.core.code_verifier import code_verifier
from app.schemas.verification import CodeLifecycleState


def test_sequencing_dag_repair_loop_bounded_termination():
    """
    Bounded Loop Test: Verifies that when an LLM repeatedly returns a cyclic DAG,
    the sequencing agent terminates strictly at max_repair_retries (default 2)
    and produces a valid deterministic fallback DAG rather than hanging indefinitely.
    """
    cyclic_json = '{"steps": [{"step_num": 1, "component_name": "a", "dependencies": ["b"]}, {"step_num": 2, "component_name": "b", "dependencies": ["a"]}]}'

    call_count = 0

    def mock_cyclic_generate(self, prompt, model_id=None):
        nonlocal call_count
        call_count += 1
        return cyclic_json, 50

    with patch("app.core.model_router.ModelRouter.generate", mock_cyclic_generate):
        # 1 initial generation + 2 repair attempts = 3 calls max
        plan = run_sequencing_agent(max_repair_retries=2)

        # Assert bounded execution: call count must equal 3
        assert call_count == 3
        # Assert deterministic fallback produced a valid DAG
        val = DAGValidator.validate(plan.steps)
        assert val.is_valid is True
        assert len(val.execution_order) > 0


def test_code_generation_repair_budget_bounded():
    """
    Bounded Loop Test: Verifies that code verification handles unfixable code
    and cleanly marks lifecycle as FAILED without hanging.
    """
    unfixable_code = """
import torch
import torch.nn as nn

class BrokenModel(nn.Module):
    def __init__(self):
        super().__init__()
        raise RuntimeError("Persistent unfixable hardware or kernel error")

    def forward(self, x):
        return x
"""
    report = code_verifier.verify_code_ladder(unfixable_code)
    assert report.lifecycle_state == CodeLifecycleState.FAILED
    assert report.all_rungs_passed is False
    assert report.repair_feedback is not None
