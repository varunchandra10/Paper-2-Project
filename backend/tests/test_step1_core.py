import sys
import os
import pytest

# Add new_backend to python search path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from app.core.config import settings
from app.core.database import ChatDatabase
from app.core.security import hash_password, verify_password
from app.core.tracer import AgentTracer
from app.schemas.paper import PaperMetadata, PaperDocument
from app.schemas.pipeline import ExtractedParameters, FeasibilityReport
from app.schemas.chat import ChatMessageRequest


def test_core_settings():
    assert settings.PROJECT_NAME == "Synthexis AI Platform"
    assert os.path.exists(settings.STORAGE_DIR)
    assert os.path.exists(settings.PAPERS_DIR)


def test_security_hashing():
    raw_pass = "secret123"
    hashed = hash_password(raw_pass)
    assert hashed != raw_pass
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("wrongpass", hashed) is False


import tempfile

def test_database_crud():
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_db_file = os.path.join(tmp_dir, "test_db.json")
        db = ChatDatabase(db_file=test_db_file)
        db.initialize_db()

        # User creation
        usr = db.create_user("test@example.com", "hash123", "Test User")
        assert usr["email"] == "test@example.com"
        fetched = db.get_user_by_email("test@example.com")
        assert fetched["id"] == usr["id"]

        # Message saving
        msg = db.save_message("conv_123", "user", "Hello Synthexis")
        assert msg["content"] == "Hello Synthexis"
        msgs = db.get_messages("conv_123")
        assert len(msgs) == 1

        # Episodic run memory
        run_id = db.save_episodic_run("paper_01", "Remote Sensing Model", {"lr": "0.001"})
        assert run_id == "run_paper_01"
        runs = db.get_episodic_runs()
        assert len(runs) == 1
        assert runs[0]["paper_title"] == "Remote Sensing Model"


def test_tracer_telemetry():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tracer = AgentTracer(traces_dir=tmp_dir)
        tracer.start_trace("paper_01")
        tracer.log_step("paper_01", "INGESTION", "success", "Parsed PDF layout", duration_ms=100)

        traces = tracer.get_traces("paper_01")
        assert len(traces) == 2
        assert traces[1]["step_name"] == "INGESTION"


def test_pydantic_schemas():
    meta = PaperMetadata(title="Transformer Paper", year=2026)
    doc = PaperDocument(paper_id="p_1", metadata=meta)
    assert doc.metadata.title == "Transformer Paper"

    params = ExtractedParameters()
    assert params.learning_rate.value == "0.0001"

    feasibility = FeasibilityReport(overall_status="FEASIBLE")
    assert feasibility.overall_status == "FEASIBLE"

    req = ChatMessageRequest(message="Summarize paper", paper_id="p_1")
    assert req.message == "Summarize paper"


if __name__ == "__main__":
    print("Running Step 1 unit tests manually...")
    test_core_settings()
    test_security_hashing()
    test_pydantic_schemas()
    print("All manual assertions passed successfully!")
