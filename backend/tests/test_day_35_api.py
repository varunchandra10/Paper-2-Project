import os
import sys
import unittest
from fastapi.testclient import TestClient

# ---- PATH SETUP ----
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app import app, db


class TestDay35ConversationPersistenceAPI(unittest.TestCase):
    """Tests the conversation persistence endpoints in the FastAPI app

    using fastapi.testclient.TestClient.
    """

    def setUp(self):
        self.client = TestClient(app)
        
        # Override the database file target to a temporary test file
        self.test_fallback_file = os.path.join(BACKEND_DIR, "papers", "chat_memory_db_api_test.json")
        db.fallback_file = self.test_fallback_file
        
        # Force local JSON database mode for reliable isolated testing
        db.use_fallback = True
        
        # Clean up any existing file and re-initialize
        if os.path.exists(self.test_fallback_file):
            os.remove(self.test_fallback_file)
        db.initialize_db()

    def tearDown(self):
        # Clean up test file
        if os.path.exists(self.test_fallback_file):
            os.remove(self.test_fallback_file)

    def test_user_authentication_flow(self):
        """Verifies registration and login validation endpoints."""
        username = "dev_tester"
        password = "TestingPass2026!"
        
        # 1. Register User
        resp = self.client.post("/users/register", json={"username": username, "password": password})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("user_id", data)
        self.assertEqual(data["username"], username)
        self.assertEqual(data["status"], "registered")
        
        user_id = data["user_id"]
        
        # 2. Register Duplicate User (should fail with 400 Bad Request)
        resp_dup = self.client.post("/users/register", json={"username": username, "password": "different_password"})
        self.assertEqual(resp_dup.status_code, 400)

        # 3. Successful Login
        resp_login = self.client.post("/users/login", json={"username": username, "password": password})
        self.assertEqual(resp_login.status_code, 200)
        login_data = resp_login.json()
        self.assertEqual(login_data["user_id"], user_id)
        self.assertEqual(login_data["status"], "authenticated")

        # 4. Failed Login (invalid credentials should return 401 Unauthorized)
        resp_fail = self.client.post("/users/login", json={"username": username, "password": "WrongPassword"})
        self.assertEqual(resp_fail.status_code, 401)

    def test_conversation_endpoints_flow(self):
        """Verifies full conversation management, message listings, renames, and cascades deletes."""
        # Setup test user and project
        user_id = db.add_user("test_conv_user", "MyUserPass")
        project_id = db.create_project("Bitemporal Adapter Workspace", "Testing change features adapter mapping")
        
        # 1. Create Conversation
        payload = {
            "user_id": user_id,
            "title": "Initial Change Detection Architecture",
            "project_id": project_id
        }
        resp = self.client.post("/conversations", json=payload)
        self.assertEqual(resp.status_code, 200)
        conv_data = resp.json()
        self.assertIn("conversation_id", conv_data)
        conv_id = conv_data["conversation_id"]

        # 2. List Conversations
        resp_list = self.client.get(f"/conversations?user_id={user_id}")
        self.assertEqual(resp_list.status_code, 200)
        convs = resp_list.json()
        self.assertEqual(len(convs), 1)
        self.assertEqual(convs[0]["conversation_id"], conv_id)
        self.assertEqual(convs[0]["title"], "Initial Change Detection Architecture")

        # 3. Save User & Assistant Messages
        resp_msg1 = self.client.post(
            f"/conversations/{conv_id}/messages",
            json={"role": "user", "content": "How do we handle temporal scale changes?"}
        )
        self.assertEqual(resp_msg1.status_code, 200)
        self.assertEqual(resp_msg1.json()["status"], "saved")
        
        resp_msg2 = self.client.post(
            f"/conversations/{conv_id}/messages",
            json={"role": "assistant", "content": "Using a Feature Pyramid Network fusion adapter helps."}
        )
        self.assertEqual(resp_msg2.status_code, 200)
        self.assertEqual(resp_msg2.json()["status"], "saved")

        # 4. Add Summary
        db.save_summary(conv_id, "User asked about temporal scale; assistant recommended FPN adapters.")

        # 5. Load Conversation Detail (should fetch messages and summary)
        resp_detail = self.client.get(f"/conversations/{conv_id}")
        self.assertEqual(resp_detail.status_code, 200)
        detail = resp_detail.json()
        self.assertEqual(detail["conversation_id"], conv_id)
        self.assertEqual(len(detail["messages"]), 2)
        self.assertEqual(detail["messages"][0]["role"], "user")
        self.assertEqual(detail["messages"][0]["content"], "How do we handle temporal scale changes?")
        self.assertEqual(detail["messages"][1]["role"], "assistant")
        self.assertEqual(detail["messages"][1]["content"], "Using a Feature Pyramid Network fusion adapter helps.")
        self.assertEqual(detail["summary"], "User asked about temporal scale; assistant recommended FPN adapters.")

        # 6. Rename Conversation
        resp_rename = self.client.put(f"/conversations/{conv_id}", json={"title": "FPN Adapters Architecture"})
        self.assertEqual(resp_rename.status_code, 200)
        self.assertEqual(resp_rename.json()["status"], "success")
        
        # Verify title change in list
        resp_list2 = self.client.get(f"/conversations?user_id={user_id}")
        self.assertEqual(resp_list2.json()[0]["title"], "FPN Adapters Architecture")

        # 7. Delete Conversation
        resp_del = self.client.delete(f"/conversations/{conv_id}")
        self.assertEqual(resp_del.status_code, 200)
        self.assertEqual(resp_del.json()["status"], "success")
        
        # Verify listing returns empty list
        resp_list_final = self.client.get(f"/conversations?user_id={user_id}")
        self.assertEqual(len(resp_list_final.json()), 0)


if __name__ == "__main__":
    unittest.main()
