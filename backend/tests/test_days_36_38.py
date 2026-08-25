import os
import sys
import unittest
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# ---- PATH SETUP ----
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app import app, db, chat_manager


class TestDays36To38ContextSummariesMemory(unittest.TestCase):
    """Tests Phase 9 Days 36-38: prompt compilation, dynamic summarization,

    memory fact extraction, and chat API routing.
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

    def tearDown(self):
        # Clean up test files
        for f in [self.test_fallback_file, self.test_vector_file]:
            if os.path.exists(f):
                os.remove(f)

    @patch("core.chat_manager.ollama.generate")
    def test_context_assembly_prompt(self, mock_generate):
        """Verifies that the compiled chat prompt correctly incorporates summary, facts, and RAG context."""
        # Setup mock user, project, conversation
        user_id = db.add_user("dev_assistant_tester", "MyPass123")
        project_id = db.create_project("SAR project")
        conv_id = db.create_conversation(user_id, "Temporal Alignment Thread", project_id)
        
        # Add a rolling summary
        db.save_summary(conv_id, "Prior summary mapping SiamU-Net configurations.")
        
        # Add memory facts
        db.add_memory_fact(user_id, "User prefers PyTorch framework", "preference")
        
        # Add mock RAG vector data into vector database fallback
        vdb_data = {
            "papers": {
                "paper_1": {
                    "paper_id": "paper_1",
                    "title": "A SiamU-Net paper",
                    "authors": "Author A",
                    "abstract": "Abstract A",
                    "metadata_json": {}
                }
            },
            "chunks": [
                {
                    "chunk_id": "chunk_1",
                    "paper_id": "paper_1",
                    "content": "SiamU-Net employs weight sharing and spatial temporal feature extraction.",
                    "section": "Method",
                    "subsection": "Backbone",
                    "page": 3,
                    "content_type": "text",
                    "source_id": "p3_b4",
                    "embedding": [0.1] * 768
                }
            ]
        }
        chat_manager.vector_db._write_fallback_data(vdb_data)

        # Build prompt using chat_manager
        with patch("core.chat_manager.generate_local_embedding", return_value=[0.1]*768):
            prompt = chat_manager.build_context_prompt(
                conversation_id=conv_id,
                user_id=user_id,
                query="How does SiamU-Net share weights?",
                paper_id="paper_1"
            )
            
        # Verify contexts are embedded in prompt
        self.assertIn("Prior summary mapping SiamU-Net configurations.", prompt)
        self.assertIn("User prefers PyTorch framework", prompt)
        self.assertIn("SiamU-Net employs weight sharing", prompt)
        self.assertIn("How does SiamU-Net share weights?", prompt)

    @patch("core.chat_manager.ollama.generate")
    def test_dynamic_summarizer(self, mock_generate):
        """Verifies that conversation history gets summarized when it exceeds 10 messages."""
        user_id = db.add_user("dev_assistant_tester", "MyPass123")
        project_id = db.create_project("SAR project")
        conv_id = db.create_conversation(user_id, "Temporal Alignment Thread", project_id)

        # Append 11 messages to exceed threshold
        for i in range(11):
            role = "user" if i % 2 == 0 else "assistant"
            db.save_message(conv_id, role, f"Message content {i}")
            
        # Mock summary generator return value
        mock_generate.return_value = {"response": "Mocked rolling conversation summary."}
        
        # Trigger summarization
        chat_manager.summarize_conversation_if_needed(conv_id)
        
        # Assert summary was saved
        saved_summary = db.get_summary(conv_id)
        self.assertEqual(saved_summary, "Mocked rolling conversation summary.")

    @patch("core.chat_manager.ollama.generate")
    def test_memory_facts_extraction(self, mock_generate):
        """Verifies parsing and deduplication of memory facts from user messages."""
        user_id = db.add_user("dev_assistant_tester", "MyPass123")
        
        # Mock Ollama returning a JSON facts list
        mock_generate.return_value = {
            "response": json.dumps([
                {"fact": "User is building change adapter model", "category": "preference"},
                {"fact": "Local system has 8GB VRAM constraint", "category": "constraint"}
            ])
        }
        
        chat_manager.extract_and_save_facts(user_id, "I only have 8GB VRAM for my model.")
        
        # Assert facts saved
        facts = db.get_memory_facts(user_id)
        self.assertEqual(len(facts), 2)
        self.assertEqual(facts[0]["fact"], "User is building change adapter model")
        self.assertEqual(facts[1]["fact"], "Local system has 8GB VRAM constraint")
        
        # Run fact extractor again with same mock (should deduplicate and not append again)
        chat_manager.extract_and_save_facts(user_id, "I only have 8GB VRAM for my model.")
        facts_after = db.get_memory_facts(user_id)
        self.assertEqual(len(facts_after), 2)

    @patch("core.chat_manager.ollama.generate")
    def test_full_chat_api_endpoint(self, mock_generate):
        """Verifies full FastAPI chat endpoint integration (saves message, responds, and archives reply)."""
        user_id = db.add_user("dev_assistant_tester", "MyPass123")
        conv_id = db.create_conversation(user_id, "Temporal Alignment Thread")
        
        # Mock LLM reply
        mock_generate.return_value = {"response": "Using SiamU-Net is recommended."}
        
        # Make API Call
        payload = {
            "content": "Which architecture is best?",
            "paper_id": "paper_1"
        }
        resp = self.client.post(f"/conversations/{conv_id}/chat", json=payload)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["response"], "Using SiamU-Net is recommended.")
        
        # Verify messages in DB
        messages = db.get_messages(conv_id)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "user")
        self.assertEqual(messages[0]["content"], "Which architecture is best?")
        self.assertEqual(messages[1]["role"], "assistant")
        self.assertEqual(messages[1]["content"], "Using SiamU-Net is recommended.")


if __name__ == "__main__":
    unittest.main()
