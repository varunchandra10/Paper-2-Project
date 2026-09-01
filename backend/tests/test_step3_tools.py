import sys
import os
import pytest

# Add new_backend to python search path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from app.tools import get_all_tools
from app.tools.vector_search_tool import VectorSearchTool
from app.tools.scholar_search_tool import ScholarSearchTool
from app.tools.hyperparameter_tool import HyperparameterTool
from app.tools.episodic_memory_tool import EpisodicMemoryTool


def test_tool_registry():
    tools = get_all_tools()
    assert "search_paper_chunks" in tools or "vector_search" in tools
    assert "search_scholar_literature" in tools
    assert "get_hyperparameters" in tools
    assert "query_episodic_memory" in tools
    assert len(tools) >= 4


def test_vector_search_tool():
    tool = VectorSearchTool()
    res = tool.run(query="remote sensing", paper_id="test_paper")
    assert isinstance(res, str)
    assert len(res) > 0


def test_scholar_search_tool():
    tool = ScholarSearchTool()
    res = tool.run(query="Change detection foundation models")
    assert isinstance(res, str)
    assert len(res) > 0


def test_hyperparameter_tool():
    tool = HyperparameterTool()
    res = tool.run(paper_id="non_existent_paper")
    assert "No extracted hyperparameter file found" in res


def test_episodic_memory_tool():
    tool = EpisodicMemoryTool()
    res = tool.run(query="")
    assert isinstance(res, str)
    assert len(res) > 0


if __name__ == "__main__":
    print("Running Step 3 Diagnostic Tools tests...")
    test_tool_registry()
    test_vector_search_tool()
    test_scholar_search_tool()
    test_hyperparameter_tool()
    test_episodic_memory_tool()
    print("All Step 3 Diagnostic Tools tests passed successfully!")
