import os
import sys
import json
import unittest
import io
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# ---- PATH SETUP ----
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app import app, db, chat_manager, extraction_jobs


class TestPhase11FastapiSse(unittest.TestCase):
    """Tests Phase 11 FastAPI & Server-Sent Events (SSE) integration:

    auth/project endpoints, paper uploads, async tasks queuing, and SSE log streams.
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
        
        # Clear jobs registry
        extraction_jobs.clear()

    def tearDown(self):
        # Clean up test files
        for f in [self.test_fallback_file, self.test_vector_file]:
            if os.path.exists(f):
                os.remove(f)

    def test_project_api_endpoints(self):
        """Verifies projects creation and listings."""
        # 1. Create project
        resp = self.client.post("/projects", json={"name": "Swin-Transformer Project", "description": "Analyzing Swin-T VRAM usage"})
        self.assertEqual(resp.status_code, 200)
        proj_id = resp.json()["project_id"]
        self.assertTrue(proj_id.startswith("project_") or len(proj_id) > 10)
        
        # 2. List projects
        list_resp = self.client.get("/projects")
        self.assertEqual(list_resp.status_code, 200)
        projects = list_resp.json()
        self.assertEqual(len(projects), 1)
        self.assertEqual(projects[0]["name"], "Swin-Transformer Project")

    def test_papers_api_endpoints(self):
        """Verifies paper listing and detail retrieval."""
        # Add mock paper
        db_data = {
            "papers": {
                "paper_1": {
                    "paper_id": "paper_1",
                    "title": "Mock Paper Title",
                    "authors": "Author A",
                    "abstract": "Abstract A",
                    "metadata": {}
                }
            },
            "chunks": []
        }
        chat_manager.vector_db._write_fallback_data(db_data)

        # 1. List papers
        resp = self.client.get("/papers")
        self.assertEqual(resp.status_code, 200)
        papers = resp.json()
        self.assertEqual(len(papers), 1)
        self.assertEqual(papers[0]["title"], "Mock Paper Title")

        # 2. Get paper details
        detail_resp = self.client.get("/papers/paper_1")
        self.assertEqual(detail_resp.status_code, 200)
        self.assertEqual(detail_resp.json()["title"], "Mock Paper Title")

        # 3. Paper not found
        missing_resp = self.client.get("/papers/missing_paper")
        self.assertEqual(missing_resp.status_code, 404)

    @patch("pipeline.graph.stream")
    def test_paper_upload_and_sse_streaming(self, mock_stream):
        """Verifies that PDF upload registers an async extraction job

        and extraction SSE endpoint streams sequential progress events.
        """
        # Set up mock LangGraph stream returns to immediately trigger node logs mapping
        mock_stream.return_value = [
            {"ingestion": {}},
            {"decomposition": {}},
            {"code_generation": {}},
            {"static_check": {}},
            {"report": {}}
        ]
        
        # Simulate upload file payload
        pdf_content = b"%PDF-1.4 Mock PDF Content"
        file_payload = {"file": ("test_paper.pdf", io.BytesIO(pdf_content), "application/pdf")}
        
        # We pass BackgroundTasks to test in-process background execution synchronous loop
        resp = self.client.post("/papers/upload", files=file_payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "queued")
        job_id = data["job_id"]
        paper_id = data["paper_id"]
        
        # Verify job registered
        self.assertIn(job_id, extraction_jobs)
        self.assertEqual(extraction_jobs[job_id]["paper_id"], paper_id)
        
        # Directly invoke the background runner synchrony helper to populate job logs
        from app import run_pipeline_in_background
        upload_path = os.path.join(BACKEND_DIR, "papers", "uploads", f"{paper_id}.pdf")
        
        run_pipeline_in_background(
            job_id=job_id,
            pdf_path=upload_path,
            constraints={},
            model_name="qwen2.5-coder:1.5b",
            paper_id=paper_id
        )
        
        # Verify job completed and logs populated
        job_info = extraction_jobs[job_id]
        self.assertEqual(job_info["status"], "completed")
        self.assertEqual(job_info["progress"], 100)
        self.assertIn("EXTRACTION_STARTED", job_info["logs"])
        self.assertIn("SECTION_DETECTED", job_info["logs"])
        self.assertIn("RAG_READY", job_info["logs"])
        self.assertIn("ANALYSIS_STARTED", job_info["logs"])
        self.assertIn("CODE_GENERATION_STARTED", job_info["logs"])
        self.assertIn("VERIFICATION_STARTED", job_info["logs"])
        self.assertIn("COMPLETED", job_info["logs"])

        # Test the SSE Streaming HTTP response
        # Using Client stream method to parse text event streams chunk lines
        with self.client.stream("GET", f"/extraction/stream/{job_id}") as stream_resp:
            self.assertEqual(stream_resp.status_code, 200)
            self.assertTrue(stream_resp.headers["content-type"].startswith("text/event-stream"))
            
            lines = [line for line in stream_resp.iter_lines() if line]
            
            # SSE chunks are formatted like:
            # event: EXTRACTION_STARTED
            # data: {"progress": 100, "status": "completed", ...}
            # Verify basic presence of events in SSE text lines stream output
            self.assertTrue(any("EXTRACTION_STARTED" in l for l in lines))
            self.assertTrue(any("SECTION_DETECTED" in l for l in lines))
            self.assertTrue(any("RAG_READY" in l for l in lines))
            self.assertTrue(any("CODE_GENERATION_STARTED" in l for l in lines))
            self.assertTrue(any("COMPLETED" in l for l in lines))


if __name__ == "__main__":
    unittest.main()
