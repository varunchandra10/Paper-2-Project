import pytest
from unittest.mock import MagicMock, patch
from app.agents.code_gen_agent import (
    validate_python_syntax,
    validate_cross_file_imports,
    run_code_gen_agent
)


def test_validate_python_syntax():
    valid_code = "import torch\nimport torch.nn as nn\nclass MyNet(nn.Module):\n    pass\n"
    ok, msg = validate_python_syntax(valid_code)
    assert ok is True
    assert "OK" in msg

    invalid_code = "def broken(\n    x = 1"
    ok, msg = validate_python_syntax(invalid_code)
    assert ok is False
    assert "SyntaxError" in msg


def test_validate_cross_file_imports_success():
    codebase = {
        "models/resnet.py": """
import torch
import torch.nn as nn

class ResNetBackbone(nn.Module):
    def __init__(self):
        super().__init__()

class ClassifierHead(nn.Module):
    def __init__(self):
        super().__init__()
""",
        "train.py": """
import torch
from models.resnet import ResNetBackbone, ClassifierHead

def train():
    model = ResNetBackbone()
    head = ClassifierHead()
""",
        "evaluate.py": """
import torch
from models.resnet import ResNetBackbone

def evaluate():
    model = ResNetBackbone()
"""
    }

    result = validate_cross_file_imports(codebase)
    assert result["valid"] is True
    assert len(result["errors"]) == 0
    assert "models/resnet.py" in result["model_exports"]
    assert "ResNetBackbone" in result["model_exports"]["models/resnet.py"]
    assert "ClassifierHead" in result["model_exports"]["models/resnet.py"]


def test_validate_cross_file_imports_missing_symbol():
    codebase = {
        "models/resnet.py": """
import torch
import torch.nn as nn

class RealResNet(nn.Module):
    pass
""",
        "train.py": """
import torch
from models.resnet import NonExistentModel

def train():
    model = NonExistentModel()
"""
    }

    result = validate_cross_file_imports(codebase)
    assert result["valid"] is False
    assert len(result["errors"]) == 1
    assert "NonExistentModel" in result["errors"][0]
    assert "train.py" in result["errors"][0]


def test_run_code_gen_agent_iterative_reflexion():
    """Verify that when candidate has errors, reflexion loop attempts repair up to max_retries."""
    mock_dual_candidates = {
        "gemini": {"code": "def broken(\n   x = 1"},
        "huggingface": {"code": "def also_broken(\n   y = 2"}
    }
    repaired_code = """
import torch
import torch.nn as nn

class FixedModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Linear(512, 10)
    def forward(self, x):
        return self.fc(x)
"""

    with patch("app.agents.code_gen_agent.dual_code_engine.generate_dual_candidates_sync", return_value=mock_dual_candidates), \
         patch("app.agents.code_gen_agent.ModelRouter") as mock_router_cls, \
         patch("app.agents.code_gen_agent.DEFAULT_PIPELINE_FILES", ["models/test_model.py"]):

        mock_router_instance = MagicMock()
        mock_router_instance.generate.return_value = (f"```python\n{repaired_code}\n```", {})
        mock_router_cls.return_value = mock_router_instance

        res = run_code_gen_agent(component_name="TestModel")
        assert "models/test_model.py" in res["codebase_files"]
        eval_info = res["code_evaluations"]["models/test_model.py"]
        # Should show reflexion repaired
        assert "Reflexion Repaired" in eval_info["engine_used"]
        assert eval_info["is_valid"] is True
        assert res["import_validation"]["valid"] is True
