import os
import sys
import unittest
import json
import tempfile
import shutil

# Add backend dir to import paths
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from app import app, db

class TestLocalAuthFlow(unittest.TestCase):
    def setUp(self):
        # Set up a clean, temporary fallback database
        self.temp_dir = tempfile.mkdtemp()
        self.old_fallback_file = db.fallback_file
        db.fallback_file = os.path.join(self.temp_dir, "test_chat_memory_db.json")
        db.initialize_db()
        self.client = TestClient(app)

    def tearDown(self):
        # Clean up temporary database directory
        shutil.rmtree(self.temp_dir)
        db.fallback_file = self.old_fallback_file

    def test_local_registration_flow(self):
        # 1. Post registration payload
        payload = {
            "username": "Test Developer",
            "email": "test@example.com"
        }
        resp = self.client.post("/auth/local-login", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["username"], "Test Developer")
        self.assertEqual(data["email"], "test@example.com")
        self.assertEqual(data["user_id"], "user_test_developer")

        # 2. Confirm stored in local flat database
        db_data = db._load_fallback()
        self.assertIn("user_test_developer", db_data["users"])
        user_info = db_data["users"]["user_test_developer"]
        self.assertEqual(user_info["username"], "Test Developer")
        self.assertEqual(user_info["email"], "test@example.com")

        # 3. Repeat request with same username (should succeed and return user info)
        resp2 = self.client.post("/auth/local-login", json=payload)
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2.json()["user_id"], "user_test_developer")

    def test_local_registration_validation(self):
        # Test empty input values
        payload = {
            "username": "",
            "email": "test@example.com"
        }
        resp = self.client.post("/auth/local-login", json=payload)
        self.assertEqual(resp.status_code, 400)

if __name__ == "__main__":
    unittest.main()
