import pytest
from unittest.mock import patch, MagicMock
from app.core.dual_code_engine import DualCodeEngine, validate_code_syntax, extract_python_code


def test_extract_python_code_markdown_blocks():
    text = "Here is the code:\n```python\nimport torch\nx = torch.randn(2, 3)\n```\nDone."
    assert extract_python_code(text) == "import torch\nx = torch.randn(2, 3)"


def test_validate_code_syntax_valid():
    valid_code = (
        "import torch\n"
        "import torch.nn as nn\n"
        "class Model(nn.Module):\n"
        "    def forward(self, x):\n"
        "        return x * 2\n"
    )
    is_valid, err = validate_code_syntax(valid_code)
    assert is_valid is True
    assert err is None


def test_validate_code_syntax_syntax_error():
    invalid_code = "def broken_func(:\n    return 42"
    is_valid, err = validate_code_syntax(invalid_code)
    assert is_valid is False
    assert "SyntaxError" in err


def test_validate_code_syntax_banned_primitives():
    unsafe_code = "import os\nos.system('echo dangerous')"
    is_valid, err = validate_code_syntax(unsafe_code)
    assert is_valid is False
    assert "Security violation" in err
    assert "os.system" in err

    subprocess_code = "import subprocess\nsubprocess.run(['ls'])"
    is_valid_sub, err_sub = validate_code_syntax(subprocess_code)
    assert is_valid_sub is False
    assert "Security violation" in err_sub


def test_dual_code_engine_primary_hf_success():
    engine = DualCodeEngine()
    mock_candidates = {
        "huggingface": {
            "code": "import torch\nx = torch.tensor([1, 2])",
            "raw": "```python\nimport torch\nx = torch.tensor([1, 2])\n```",
            "valid": True
        },
        "gemini": {
            "code": "import torch\ny = torch.tensor([3, 4])",
            "raw": "```python\nimport torch\ny = torch.tensor([3, 4])\n```",
            "valid": True
        }
    }
    with patch.object(engine, "generate_dual_candidates_sync", return_value=mock_candidates):
        content, label = engine.generate_paper_code_response("write code")
        assert "x = torch.tensor([1, 2])" in content
        assert "Hugging Face" in label


def test_dual_code_engine_failover_to_gemini_on_hf_syntax_error():
    engine = DualCodeEngine()
    mock_candidates = {
        "huggingface": {
            "code": "def broken_syntax(:\n    pass",
            "raw": "```python\ndef broken_syntax(:\n    pass\n```",
            "valid": False
        },
        "gemini": {
            "code": "import torch\nclass Net:\n    pass",
            "raw": "```python\nimport torch\nclass Net:\n    pass\n```",
            "valid": True
        }
    }
    with patch.object(engine, "generate_dual_candidates_sync", return_value=mock_candidates):
        content, label = engine.generate_paper_code_response("write code")
        assert "class Net:" in content
        assert "Google Gemini" in label
        assert "Failover" in label


def test_dual_code_engine_both_syntax_error_triggers_repair():
    engine = DualCodeEngine()
    mock_candidates = {
        "huggingface": {
            "code": "def bad1(:\n    pass",
            "raw": "```python\ndef bad1(:\n    pass\n```",
            "valid": False
        },
        "gemini": {
            "code": "def bad2(:\n    pass",
            "raw": "```python\ndef bad2(:\n    pass\n```",
            "valid": False
        }
    }
    repaired_code = "def fixed_func():\n    return 42"
    with patch.object(engine, "generate_dual_candidates_sync", return_value=mock_candidates), \
         patch.object(engine, "repair_code_syntax_sync", return_value=(repaired_code, "Google Gemini")):
        content, label = engine.generate_paper_code_response("write code")
        assert "fixed_func" in content
        assert "Auto-Repaired" in label
