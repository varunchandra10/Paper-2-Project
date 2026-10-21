import pytest
from app.schemas.pipeline import BuildSequenceStep, BuildSequence
from app.core.dag_validator import DAGValidator, DAGErrorCode, DAGValidationResult


def test_valid_dag_topological_sort():
    steps = [
        BuildSequenceStep(step_num=1, component_name="config", description="Config", dependencies=[]),
        BuildSequenceStep(step_num=2, component_name="dataset", description="Dataset", dependencies=["config"]),
        BuildSequenceStep(step_num=3, component_name="encoder", description="Encoder", dependencies=["dataset"]),
        BuildSequenceStep(step_num=4, component_name="fusion", description="Fusion", dependencies=["encoder"]),
        BuildSequenceStep(step_num=5, component_name="loss", description="Loss", dependencies=["fusion"]),
        BuildSequenceStep(step_num=6, component_name="trainer", description="Trainer", dependencies=["dataset", "fusion", "loss"])
    ]
    res = DAGValidator.validate(steps)
    assert res.is_valid is True
    assert len(res.issues) == 0
    assert res.execution_order == ["config", "dataset", "encoder", "fusion", "loss", "trainer"]


def test_deterministic_tie_breaking():
    # Both zebra_node and alpha_node have in-degree 0; tie-breaking must be strictly alphabetical
    steps_order_1 = [
        BuildSequenceStep(step_num=1, component_name="zebra_node", description="Zebra", dependencies=[]),
        BuildSequenceStep(step_num=2, component_name="alpha_node", description="Alpha", dependencies=[]),
        BuildSequenceStep(step_num=3, component_name="consumer", description="Consumer", dependencies=["zebra_node", "alpha_node"])
    ]
    res1 = DAGValidator.validate(steps_order_1)
    assert res1.is_valid is True
    assert res1.execution_order == ["alpha_node", "zebra_node", "consumer"]

    steps_order_2 = [
        BuildSequenceStep(step_num=1, component_name="consumer", description="Consumer", dependencies=["zebra_node", "alpha_node"]),
        BuildSequenceStep(step_num=2, component_name="alpha_node", description="Alpha", dependencies=[]),
        BuildSequenceStep(step_num=3, component_name="zebra_node", description="Zebra", dependencies=[]),
    ]
    res2 = DAGValidator.validate(steps_order_2)
    assert res2.is_valid is True
    assert res2.execution_order == ["alpha_node", "zebra_node", "consumer"]


def test_cycle_detection_direct_loop():
    # A -> B -> A
    steps = [
        BuildSequenceStep(step_num=1, component_name="node_a", description="A", dependencies=["node_b"]),
        BuildSequenceStep(step_num=2, component_name="node_b", description="B", dependencies=["node_a"])
    ]
    res = DAGValidator.validate(steps)
    assert res.is_valid is False
    codes = [i.code for i in res.issues]
    assert DAGErrorCode.CYCLE_DETECTED in codes
    assert res.cycle_path is not None
    assert set(res.cycle_path) == {"node_a", "node_b"}


def test_cycle_detection_indirect_loop():
    # A -> B -> C -> A
    steps = [
        BuildSequenceStep(step_num=1, component_name="node_a", description="A", dependencies=["node_c"]),
        BuildSequenceStep(step_num=2, component_name="node_b", description="B", dependencies=["node_a"]),
        BuildSequenceStep(step_num=3, component_name="node_c", description="C", dependencies=["node_b"])
    ]
    res = DAGValidator.validate(steps)
    assert res.is_valid is False
    codes = [i.code for i in res.issues]
    assert DAGErrorCode.CYCLE_DETECTED in codes
    assert res.cycle_path is not None
    assert len(res.cycle_path) >= 3


def test_self_dependency_detection():
    # Node depends on itself
    steps = [
        BuildSequenceStep(step_num=1, component_name="self_loop", description="Loop", dependencies=["self_loop"])
    ]
    res = DAGValidator.validate(steps)
    assert res.is_valid is False
    codes = [i.code for i in res.issues]
    assert DAGErrorCode.SELF_DEPENDENCY in codes


def test_duplicate_node_detection():
    steps = [
        BuildSequenceStep(step_num=1, component_name="encoder", description="Encoder 1", dependencies=[]),
        BuildSequenceStep(step_num=2, component_name="encoder", description="Encoder 2", dependencies=[])
    ]
    res = DAGValidator.validate(steps)
    assert res.is_valid is False
    codes = [i.code for i in res.issues]
    assert DAGErrorCode.DUPLICATE_NODE in codes


def test_missing_dependency_detection():
    steps = [
        BuildSequenceStep(step_num=1, component_name="trainer", description="Trainer", dependencies=["phantom_dataset"])
    ]
    res = DAGValidator.validate(steps)
    assert res.is_valid is False
    codes = [i.code for i in res.issues]
    assert DAGErrorCode.MISSING_DEPENDENCY in codes
    missing_issue = next(i for i in res.issues if i.code == DAGErrorCode.MISSING_DEPENDENCY)
    assert missing_issue.details.get("missing_dependency") == "phantom_dataset"


def test_orphan_node_detection():
    steps = [
        BuildSequenceStep(step_num=1, component_name="config", description="Config", dependencies=[]),
        BuildSequenceStep(step_num=2, component_name="model", description="Model", dependencies=["config"]),
        # Orphan node: completely disconnected from the rest of the plan
        BuildSequenceStep(step_num=3, component_name="isolated_orphan", description="Orphan", dependencies=[])
    ]
    res = DAGValidator.validate(steps)
    assert res.is_valid is False
    codes = [i.code for i in res.issues]
    assert DAGErrorCode.ORPHAN_NODE in codes
    assert any(i.node_id == "isolated_orphan" for i in res.issues)


def test_invalid_node_id_detection():
    steps = [
        BuildSequenceStep(step_num=1, component_name="   ", description="Empty name", dependencies=[]),
        BuildSequenceStep(step_num=2, component_name="bad name with spaces!", description="Bad chars", dependencies=[])
    ]
    res = DAGValidator.validate(steps)
    assert res.is_valid is False
    codes = [i.code for i in res.issues]
    assert DAGErrorCode.INVALID_NODE_ID in codes


def test_empty_plan_detection():
    res = DAGValidator.validate([])
    assert res.is_valid is False
    codes = [i.code for i in res.issues]
    assert DAGErrorCode.EMPTY_PLAN in codes


def test_format_error_feedback():
    steps = [
        BuildSequenceStep(step_num=1, component_name="node_a", description="A", dependencies=["node_b"]),
        BuildSequenceStep(step_num=2, component_name="node_b", description="B", dependencies=["node_a"])
    ]
    res = DAGValidator.validate(steps)
    feedback = DAGValidator.format_error_feedback(res)
    assert "CYCLE_DETECTED" in feedback
    assert "node_a" in feedback
    assert "node_b" in feedback


def test_sequencing_agent_repair_loop(monkeypatch):
    from app.agents import sequencing_agent
    from app.core.model_router import ModelRouter

    # Simulate: Attempt 1 returns circular dependency, Attempt 2 returns valid acyclic DAG
    attempt = {"count": 0}

    def mock_generate(self, prompt, model_id=None):
        attempt["count"] += 1
        if attempt["count"] == 1:
            # Buggy cyclic JSON
            return '{"steps": [{"step_num": 1, "component_name": "a", "dependencies": ["b"]}, {"step_num": 2, "component_name": "b", "dependencies": ["a"]}]}', 100
        else:
            # Corrected acyclic JSON
            return '{"steps": [{"step_num": 1, "component_name": "a", "dependencies": []}, {"step_num": 2, "component_name": "b", "dependencies": ["a"]}]}', 100

    monkeypatch.setattr(ModelRouter, "generate", mock_generate)

    seq = sequencing_agent.run_sequencing_agent(max_repair_retries=2)
    assert attempt["count"] == 2  # Repaired on attempt 2!
    assert seq.total_steps == 2
    step_names = [s.component_name for s in seq.steps]
    assert step_names == ["a", "b"]
    assert seq.steps[0].step_num == 1
    assert seq.steps[1].step_num == 2


def test_sequencing_agent_fallback_on_unrepairable_plan(monkeypatch):
    from app.agents import sequencing_agent
    from app.core.model_router import ModelRouter

    # Simulate: All attempts return unparseable garbage or persistent cycle
    def mock_generate(self, prompt, model_id=None):
        return 'Not valid JSON at all!', 50

    monkeypatch.setattr(ModelRouter, "generate", mock_generate)

    seq = sequencing_agent.run_sequencing_agent(max_repair_retries=1)
    # Verified fallback DAG used
    assert seq.total_steps == 6
    step_names = [s.component_name for s in seq.steps]
    assert step_names == ["config", "dataset", "encoder", "fusion", "loss", "trainer"]
