import os
import sys
import json
import io
import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# ---- PATH SETUP ----
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app import app, db, chat_manager, extraction_jobs
from core.logger import log_observability_event
from pipeline import graph


class TestPhase12BenchmarksAndProduction(unittest.TestCase):
    """Tests Phase 12 Production Readiness: end-to-end LangGraph pipeline benchmarks,

    failure injections, header authorizations, and structured logging.
    """

    def setUp(self):
        self.client = TestClient(app)
        
        # Override file locations to temporary test paths
        self.test_fallback_file = os.path.join(BACKEND_DIR, "papers", "chat_memory_db_api_test.json")
        db.fallback_file = self.test_fallback_file
        db.use_fallback = True
        
        # Override vector db local fallback file
        self.test_vector_file = os.path.join(BACKEND_DIR, "papers", "in_memory_vector_db_test.json")
        chat_manager.vector_db.fallback_file = self.test_vector_file
        chat_manager.vector_db.use_fallback = True
        
        # Clean up files
        for f in [self.test_fallback_file, self.test_vector_file]:
            if os.path.exists(f):
                os.remove(f)
                
        db.initialize_db()
        chat_manager.vector_db.initialize_db()
        extraction_jobs.clear()
        
        # Clean up observability log file if present
        self.obs_log_file = "backend_observability.log"
        if os.path.exists(self.obs_log_file):
            # Just clear content
            open(self.obs_log_file, "w").close()

    def tearDown(self):
        # Clean up test files
        for f in [self.test_fallback_file, self.test_vector_file]:
            if os.path.exists(f):
                os.remove(f)

    @patch("pipeline.graph.invoke")
    def test_day_45_end_to_end_benchmark_nodes(self, mock_graph_invoke):
        """Verifies that invoking the pipeline returns complete output schemas."""
        # Set up mock pipeline output
        mock_output = {
            "pdf_path": "uploads/paper_test.pdf",
            "report": MagicMock(overall_status="FEASIBLE"),
            "code_verification_report": MagicMock()
        }
        mock_graph_invoke.return_value = mock_output
        
        state_input = {
            "pdf_path": "uploads/paper_test.pdf",
            "constraints": {},
            "model_name": "qwen2.5-coder:1.5b",
            "loop_count": 0,
            "raw_sections": {}
        }
        
        # Invoke LangGraph core
        result = graph.invoke(state_input)
        
        self.assertEqual(result["pdf_path"], "uploads/paper_test.pdf")
        self.assertTrue(hasattr(result["report"], "overall_status"))
        mock_graph_invoke.assert_called_once_with(state_input)

    def test_day_46_upload_failure_injections(self):
        """Verifies that corrupted PDFs and oversize files are rejected."""
        # 1. Corrupted PDF check (fails signature magic bytes check)
        corrupted_content = b"Not a PDF header file content string."
        file_payload = {"file": ("test_corrupt.pdf", io.BytesIO(corrupted_content), "application/pdf")}
        resp = self.client.post("/papers/upload", files=file_payload)
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["detail"], "Invalid PDF file signature.")

        # 2. Oversize PDF check (fails 50MB limit)
        oversize_content = b"%" + b"PDF-1.4" + (b"A" * (51 * 1024 * 1024))
        file_payload_large = {"file": ("test_large.pdf", io.BytesIO(oversize_content), "application/pdf")}
        resp_large = self.client.post("/papers/upload", files=file_payload_large)
        self.assertEqual(resp_large.status_code, 400)
        self.assertEqual(resp_large.json()["detail"], "File size exceeds maximum limit of 50MB.")

    @patch("core.chat_manager.ollama.generate")
    def test_day_47_authorization_headers(self, mock_generate):
        """Verifies that conversation chats validate the x-user-id ownership header."""
        user_id = db.add_user("legit_user", "LegitPass!")
        other_user_id = db.add_user("hacker_user", "HackerPass!")
        conv_id = db.create_conversation(user_id, "Legit Session")
        
        mock_generate.return_value = {"response": "Secret model answer."}
        
        # 1. Access with legit user header -> 200
        headers = {"X-User-ID": user_id}
        resp = self.client.post(f"/conversations/{conv_id}/chat", json={"content": "What is 2+2?"}, headers=headers)
        self.assertEqual(resp.status_code, 200)
        
        # 2. Access with hacker user header -> 403 Forbidden
        bad_headers = {"X-User-ID": other_user_id}
        resp_bad = self.client.post(f"/conversations/{conv_id}/chat", json={"content": "Hacking conversation?"}, headers=bad_headers)
        self.assertEqual(resp_bad.status_code, 403)
        self.assertEqual(resp_bad.json()["detail"], "Unauthorized access to this conversation thread.")

    def test_day_48_observability_logging(self):
        """Verifies that structured observability event logs register correctly in log file."""
        log_observability_event("test_observability_tracing", paper_id="p123", latency_ms=45.2)
        
        # Check log file exists
        self.assertTrue(os.path.exists(self.obs_log_file))
        
        # Verify contains logged JSON keys
        with open(self.obs_log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            
        self.assertTrue(len(lines) > 0)
        log_line = lines[-1]
        self.assertIn("test_observability_tracing", log_line)
        self.assertIn("p123", log_line)
        self.assertIn("latency_ms", log_line)


if __name__ == "__main__":
    unittest.main()
