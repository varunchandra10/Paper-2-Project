import sys
import os
import pytest

# Add new_backend to python search path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from app.schemas.paper import PaperDocument, PaperMetadata
from app.schemas.pipeline import ExtractedParameters, FeasibilityReport, BuildSequence
from app.agents.ingestion_agent import run_ingestion_agent, fetch_scholar_metadata
from app.agents.parameter_agent import run_parameter_agent
from app.agents.decomposition_agent import run_decomposition_agent
from app.agents.feasibility_agent import run_feasibility_agent
from app.agents.gap_agent import run_gap_agent
from app.agents.sequencing_agent import run_sequencing_agent
from app.agents.specification_agent import run_specification_agent
from app.agents.code_gen_agent import run_code_gen_agent
from app.agents.report_agent import run_report_agent
from app.agents.chat_agent import ChatAgent


def test_ingestion_agent():
    meta = run_ingestion_agent({"Abstract": "Sample deep learning paper abstract."})
    assert isinstance(meta, PaperMetadata)
    assert meta.title is not None


def test_parameter_agent():
    doc = PaperDocument(paper_id="p1", metadata=PaperMetadata(title="Test"), raw_full_text="learning_rate = 0.001, batch_size = 8")
    params = run_parameter_agent(doc)
    assert isinstance(params, ExtractedParameters)
    assert params.learning_rate.value is not None


def test_decomposition_agent():
    decomp = run_decomposition_agent({"Abstract": "test"})
    assert "components" in decomp
    assert decomp["total_components"] > 0


def test_feasibility_agent():
    cg = {"components": []}
    constraints = {"max_vram_gb": 6.0}
    report = run_feasibility_agent(cg, constraints)
    assert isinstance(report, FeasibilityReport)
    assert report.overall_status in ["FEASIBLE", "FEASIBLE_WITH_MODIFICATION", "NOT_FEASIBLE"]


def test_gap_agent():
    params = ExtractedParameters()
    gaps = run_gap_agent({"components": []}, params)
    assert "completeness_score" in gaps


def test_sequencing_agent():
    feas = FeasibilityReport()
    seq = run_sequencing_agent({"components": []}, feas)
    assert isinstance(seq, BuildSequence)
    assert seq.total_steps > 0


def test_specification_agent():
    seq = BuildSequence()
    spec = run_specification_agent(seq)
    assert "project_name" in spec


def test_code_gen_agent():
    params = ExtractedParameters()
    code = run_code_gen_agent("dataset", params)
    assert "# Grounding:" in code
    assert "class " in code


def test_report_agent():
    feas = FeasibilityReport()
    seq = BuildSequence()
    rep = run_report_agent({}, feas, seq)
    assert "summary" in rep


def test_chat_agent():
    agent = ChatAgent()
    res = agent.process_message("test_conv_99", "How do I train this model?")
    assert "content" in res
    assert res["conversation_id"] == "test_conv_99"


if __name__ == "__main__":
    print("Running Step 4 Agents unit tests...")
    test_ingestion_agent()
    test_parameter_agent()
    test_decomposition_agent()
    test_feasibility_agent()
    test_gap_agent()
    test_sequencing_agent()
    test_specification_agent()
    test_code_gen_agent()
    test_report_agent()
    test_chat_agent()
    print("All Step 4 Agents unit tests passed successfully!")
