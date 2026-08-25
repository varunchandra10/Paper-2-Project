import os
import sys
import unittest
import requests
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# ---- PATH SETUP ----
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app import app, db, chat_manager
from core.model_router import ModelRouter


class TestPhase10ModelRouter(unittest.TestCase):
    """Tests Phase 10 Model Router: task classification, local-first routing,

    external API calls, fallback hierarchies, and database metadata tracking.
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

    @patch("core.model_router.ollama.generate")
    def test_task_classification(self, mock_generate):
        """Verifies that user queries are correctly mapped to task categories."""
        router = ModelRouter()
        
        # 1. Test Code Gen prompt
        mock_generate.return_value = {"response": "code_generation"}
        category = router.classify_task("Write a python loader class.")
        self.assertEqual(category, "code_generation")
        
        # 2. Test Extraction prompt
        mock_generate.return_value = {"response": "extraction"}
        category = router.classify_task("What are the learning rates in the table?")
        self.assertEqual(category, "extraction")

    @patch("core.model_router.ollama.generate")
    def test_local_first_routing(self, mock_generate):
        """Verifies that explanation, extraction, and summaries route to local Ollama."""
        router = ModelRouter()
        mock_generate.return_value = {"response": "Local response content."}
        
        # 'explanation' should run locally
        res, model_used = router.generate_routed_response("What is SiamU-Net?", "explanation")
        self.assertEqual(res, "Local response content.")
        self.assertEqual(model_used, "Ollama (qwen2.5-coder:1.5b)")

    @patch("core.model_router.requests.post")
    @patch("core.model_router.ollama.generate")
    def test_remote_routing_and_fallbacks(self, mock_generate, mock_post):
        """Verifies that reasoning/code-gen queries try OpenRouter/Groq APIs,

        falling back hierarchically to local Ollama if APIs fail.
        """
        router = ModelRouter()
        
        # Configure API Keys dynamically for testing
        router.openrouter_api_key = "test_or_key"
        router.groq_api_key = "test_groq_key"
        
        # Scenario A: OpenRouter Primary succeeds
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"choices": [{"message": {"content": "Claude 3.5 Sonnet Response"}}]}
        mock_post.return_value = mock_resp
        
        res, model_used = router.generate_routed_response("How to debug spatial attention layers?", "debugging")
        self.assertEqual(res, "Claude 3.5 Sonnet Response")
        self.assertEqual(model_used, "OpenRouter (anthropic/claude-3.5-sonnet)")

        # Scenario B: OpenRouter fails (status 500), Groq Primary succeeds
        mock_resp_fail = MagicMock()
        mock_resp_fail.status_code = 500
        
        mock_resp_groq = MagicMock()
        mock_resp_groq.status_code = 200
        mock_resp_groq.json.return_value = {"choices": [{"message": {"content": "Llama 3.3 70B Response"}}]}
        
        # Sequence of post requests: 1st (OR Primary) -> fail, 2nd (OR Secondary) -> fail, 3rd (Groq Primary) -> success
        mock_post.side_effect = [mock_resp_fail, mock_resp_fail, mock_resp_groq]
        
        res, model_used = router.generate_routed_response("Compile a change adapter layer.", "code_generation")
        self.assertEqual(res, "Llama 3.3 70B Response")
        self.assertEqual(model_used, "Groq (llama-3.3-70b-versatile)")

        # Scenario C: All APIs fail, falls back to local Ollama
        mock_post.side_effect = [mock_resp_fail, mock_resp_fail, mock_resp_fail, mock_resp_fail]
        mock_generate.return_value = {"response": "Local Fallback Response"}
        
        res, model_used = router.generate_routed_response("Write code mapping.", "code_generation")
        self.assertEqual(res, "Local Fallback Response")
        self.assertEqual(model_used, "Ollama Fallback (qwen2.5-coder:1.5b)")

    def test_database_metadata_logging(self):
        """Verifies that model_used string column updates and retrieves properly from the database."""
        user_id = db.add_user("router_tester", "Pass123!")
        conv_id = db.create_conversation(user_id, "Model Router Session")
        
        # Save message with model_used metadata
        db.save_message(conv_id, "assistant", "Response content.", model_used="Groq (llama-3.3-70b-versatile)")
        
        # Fetch messages
        messages = db.get_messages(conv_id)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["model_used"], "Groq (llama-3.3-70b-versatile)")

    @patch("core.chat_manager.ollama.generate")
    @patch("core.model_router.ollama.generate")
    def test_fastapi_endpoint_chat_metadata(self, mock_router_generate, mock_chat_generate):
        """Verifies that the FastAPI chat endpoint returns and saves model_used metadata in the JSON response."""
        user_id = db.add_user("router_tester", "Pass123!")
        conv_id = db.create_conversation(user_id, "Model Router Session")
        
        # Mock classfier -> extraction, local Ollama response
        mock_router_generate.return_value = {"response": "extraction"}
        mock_chat_generate.return_value = {"response": "Ollama response."}
        
        resp = self.client.post(f"/conversations/{conv_id}/chat", json={
            "content": "What is the training batch size?"
        })
        
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["response"], "Ollama response.")
        self.assertEqual(data["model_used"], "Ollama (qwen2.5-coder:1.5b)")


if __name__ == "__main__":
    unittest.main()
