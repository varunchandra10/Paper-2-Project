import pytest
from langgraph.graph import END
from app.graph.state import PipelineState
from app.schemas.pipeline import FeasibilityReport, ExtractedParameters, ParameterDetails, ProvenanceStatus, BuildSequence
from app.graph.workflow import route_feasibility, route_evaluation, app_workflow
from app.graph.nodes.adaptation import parameter_adaptation_node
from app.graph.nodes.specification import specification_node
from app.graph.nodes.evaluation import evaluation_node
from app.graph.nodes.repair import code_repair_node


def test_route_feasibility_direct_pass():
    report = FeasibilityReport(
        overall_status="FEASIBLE",
        estimated_vram_gb=2.5,
        available_vram_gb=6.0,
        bottlenecks=[],
        suggested_adaptations=[]
    )
    state: PipelineState = {
        "feasibility_report": report,
        "feasibility_loop_count": 0,
        "max_feasibility_retries": 2
    }
    next_node = route_feasibility(state)
    assert next_node == "sequencing_node"


def test_route_feasibility_triggers_adaptation():
    report = FeasibilityReport(
        overall_status="NOT_FEASIBLE",
        estimated_vram_gb=12.0,
        available_vram_gb=4.0,
        bottlenecks=["VRAM severely exceeded"],
        suggested_adaptations=["Reduce batch size"]
    )
    state: PipelineState = {
        "feasibility_report": report,
        "feasibility_loop_count": 0,
        "max_feasibility_retries": 2
    }
    next_node = route_feasibility(state)
    assert next_node == "adaptation_node"


def test_route_feasibility_bounded_exit_on_max_retries():
    report = FeasibilityReport(
        overall_status="NOT_FEASIBLE",
        estimated_vram_gb=12.0,
        available_vram_gb=4.0,
        bottlenecks=["VRAM severely exceeded"],
        suggested_adaptations=["Reduce batch size"]
    )
    state: PipelineState = {
        "feasibility_report": report,
        "feasibility_loop_count": 2,
        "max_feasibility_retries": 2
    }
    # Retries reached bound -> must exit to sequencing_node, NEVER loop indefinitely
    next_node = route_feasibility(state)
    assert next_node == "sequencing_node"


def test_parameter_adaptation_node_scales_batch_size():
    params = ExtractedParameters(
        batch_size=ParameterDetails(value=16, status=ProvenanceStatus.EXPLICIT.value)
    )
    report = FeasibilityReport(
        overall_status="NOT_FEASIBLE",
        estimated_vram_gb=12.0,
        available_vram_gb=4.0,
        bottlenecks=[],
        suggested_adaptations=[]
    )
    state: PipelineState = {
        "extracted_parameters": params,
        "feasibility_report": report,
        "feasibility_loop_count": 0,
        "history_trace": []
    }

    result = parameter_adaptation_node(state)
    adapted_params = result["extracted_parameters"]
    assert adapted_params.batch_size.value == 4  # Scaled down by 4 for NOT_FEASIBLE
    assert adapted_params.batch_size.status == ProvenanceStatus.DERIVED.value
    assert adapted_params.batch_size.extraction_method == "feasibility_adaptation"
    assert result["feasibility_loop_count"] == 1
    assert len(result["history_trace"]) == 1
    assert result["history_trace"][0]["node"] == "adaptation_node"


def test_route_evaluation_direct_pass():
    state: PipelineState = {
        "verification_result": {"status": "PASSED"},
        "code_repair_loop_count": 0,
        "max_repair_retries": 2
    }
    next_node = route_evaluation(state)
    assert next_node == END


def test_route_evaluation_triggers_repair():
    state: PipelineState = {
        "verification_result": {"status": "FAILED", "error": "SyntaxError on line 5"},
        "code_repair_loop_count": 0,
        "max_repair_retries": 2
    }
    next_node = route_evaluation(state)
    assert next_node == "code_repair_node"


def test_route_evaluation_bounded_exit_on_max_retries():
    state: PipelineState = {
        "verification_result": {"status": "FAILED", "error": "Persistent runtime error"},
        "code_repair_loop_count": 2,
        "max_repair_retries": 2
    }
    # Retries reached bound -> must exit to END, NEVER loop indefinitely
    next_node = route_evaluation(state)
    assert next_node == END


def test_code_repair_node_heuristic_patch():
    # Broken code missing super().__init__()
    buggy_code = (
        "import torch\n"
        "import torch.nn as nn\n"
        "class ToyModel(nn.Module):\n"
        "    def __init__(self):\n"
        "        self.linear = nn.Linear(10, 2)\n"
        "    def forward(self, x):\n"
        "        return self.linear(x)\n"
    )
    state: PipelineState = {
        "sample_code": buggy_code,
        "verification_result": {"status": "FAILED", "error": "AttributeError: cannot assign module before Module.__init__() call"},
        "code_repair_loop_count": 0,
        "history_trace": []
    }

    result = code_repair_node(state)
    repaired_code = result["sample_code"]
    assert "super().__init__()" in repaired_code
    assert result["code_repair_loop_count"] == 1
    assert len(result["history_trace"]) == 1
    assert result["history_trace"][0]["node"] == "code_repair_node"


def test_specification_node_synthesis():
    params = ExtractedParameters(
        batch_size=ParameterDetails(value=8, status=ProvenanceStatus.DERIVED.value)
    )
    state: PipelineState = {
        "extracted_parameters": params,
        "build_sequence": BuildSequence(steps=[]),
        "history_trace": []
    }
    result = specification_node(state)
    spec = result["specification"]
    assert spec["target_framework"] == "PyTorch"
    assert "modules" in spec
    assert len(result["history_trace"]) == 1
    assert result["history_trace"][0]["node"] == "specification_node"


def test_evaluation_node_pass_on_valid_pytorch_model():
    valid_model_code = (
        "import torch\n"
        "import torch.nn as nn\n"
        "class Model(nn.Module):\n"
        "    def __init__(self, in_features=512, out_features=10):\n"
        "        super().__init__()\n"
        "        self.fc = nn.Linear(in_features, out_features)\n"
        "    def forward(self, x):\n"
        "        return self.fc(x)\n"
    )
    state: PipelineState = {
        "sample_code": valid_model_code,
        "code_repair_loop_count": 0,
        "history_trace": []
    }
    result = evaluation_node(state)
    verif = result["verification_result"]
    assert verif["layer1_syntax"] is True
    assert verif["layer3_execution"] is True
    assert verif["status"] == "PASSED"
    assert result["parameters_approved"] is True


def test_subgraph_feasibility_self_correction_cycle():
    """Simulates the feasibility -> adaptation -> feasibility self-correction loop."""
    params = ExtractedParameters(
        batch_size=ParameterDetails(value=16, status=ProvenanceStatus.EXPLICIT.value)
    )
    # 1. Feasibility node runs and discovers VRAM bottleneck with 1.80GB available
    state: PipelineState = {
        "extracted_parameters": params,
        "constraints": {"max_vram_gb": 1.80},
        "component_graph": {"components": [1, 2, 3, 4]},
        "feasibility_loop_count": 0,
        "max_feasibility_retries": 2,
        "history_trace": []
    }
    from app.graph.nodes.feasibility import feasibility_node
    res1 = feasibility_node(state)
    state.update(res1)
    assert state["feasibility_report"].overall_status == "FEASIBLE_WITH_MODIFICATION"
    assert route_feasibility(state) == "adaptation_node"

    # 2. Router routes to adaptation_node
    res2 = parameter_adaptation_node(state)
    state.update(res2)
    assert state["extracted_parameters"].batch_size.value == 8
    assert state["feasibility_loop_count"] == 1

    # 3. Graph loops back to feasibility_node to re-check
    res3 = feasibility_node(state)
    state.update(res3)
    # With batch size reduced from 16 to 8, VRAM requirements drop below 1.80GB to 1.77GB
    assert state["feasibility_report"].estimated_vram_gb < res1["feasibility_report"].estimated_vram_gb
    assert state["feasibility_report"].overall_status == "FEASIBLE"
    assert route_feasibility(state) == "sequencing_node"

    # Verify history trace logged all node transitions
    nodes_visited = [t["node"] for t in state["history_trace"]]
    assert nodes_visited == ["feasibility_node", "adaptation_node", "feasibility_node"]


def test_subgraph_code_repair_cycle():
    """Simulates the evaluation -> repair -> evaluation self-correction loop."""
    # Model initially missing super().__init__(), causing Layer 3 execution error
    initial_buggy_code = (
        "import torch\n"
        "import torch.nn as nn\n"
        "class Model(nn.Module):\n"
        "    def __init__(self, in_features=512, out_features=10):\n"
        "        self.fc = nn.Linear(in_features, out_features)\n"
        "    def forward(self, x):\n"
        "        return self.fc(x)\n"
    )
    state: PipelineState = {
        "sample_code": initial_buggy_code,
        "code_repair_loop_count": 0,
        "max_repair_retries": 2,
        "history_trace": []
    }

    # 1. Evaluation fails due to missing super call
    eval1 = evaluation_node(state)
    state.update(eval1)
    assert state["verification_result"]["status"] == "FAILED"
    assert route_evaluation(state) == "code_repair_node"

    # 2. Routes to repair node which injects super().__init__()
    rep1 = code_repair_node(state)
    state.update(rep1)
    assert "super().__init__()" in state["sample_code"]
    assert state["code_repair_loop_count"] == 1

    # 3. Loops back to evaluation node
    eval2 = evaluation_node(state)
    state.update(eval2)
    assert state["verification_result"]["status"] == "PASSED"
    assert state["parameters_approved"] is True
    assert route_evaluation(state) == END

    # Verify history trace logged the self-correcting cycle
    nodes_visited = [t["node"] for t in state["history_trace"]]
    assert nodes_visited == ["evaluation_node", "code_repair_node", "evaluation_node"]
