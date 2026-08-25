import os
import unittest
import sys
import shutil

# ---- PATH SETUP ----
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from core.security import hash_password, verify_password
from core.database import ChatDatabase


class TestDay34DatabaseFoundation(unittest.TestCase):
    """Verifies cryptographic password hashing, database initialization,

    resilient fallback mechanics, and complete CRUD operations.
    """

    def setUp(self):
        # We will test in local JSON fallback mode by directing to a temporary test file
        self.db = ChatDatabase(db_url="postgresql://invalid_user:invalid_pass@localhost:5432/non_existent_db")
        # Ensure it engaged fallback mode
        self.assertTrue(self.db.use_fallback)
        
        # Point fallback file to a dedicated test path
        self.test_fallback_file = os.path.join(BACKEND_DIR, "papers", "chat_memory_db_test.json")
        self.db.fallback_file = self.test_fallback_file
        
        # Clean up any existing test file
        if os.path.exists(self.test_fallback_file):
            os.remove(self.test_fallback_file)
            
        self.db.initialize_db()

    def tearDown(self):
        # Clean up test file
        if os.path.exists(self.test_fallback_file):
            os.remove(self.test_fallback_file)

    def test_password_security(self):
        """Verifies cryptographically secure password hashing and verification."""
        password = "SuperSecretPassword123!"
        
        # Generate hash
        pwd_hash = hash_password(password)
        self.assertIsNotNone(pwd_hash)
        self.assertIn("$", pwd_hash)
        
        # Verify correct credentials
        self.assertTrue(verify_password(pwd_hash, password))
        
        # Verify incorrect credentials
        self.assertFalse(verify_password(pwd_hash, "WrongPassword"))
        self.assertFalse(verify_password(pwd_hash, ""))

    def test_database_crud_operations(self):
        """Tests registration, retrieval, cascading deletions, summaries, and memory."""
        # 1. Register Users
        user_id = self.db.add_user("test_dev_agent", "SecureAgentPass")
        self.assertIsNotNone(user_id)
        
        # Duplicate user check should raise ValueError
        with self.assertRaises(ValueError):
            self.db.add_user("test_dev_agent", "AnotherPass")
            
        # Verify user
        verified_uid = self.db.verify_user("test_dev_agent", "SecureAgentPass")
        self.assertEqual(verified_uid, user_id)
        
        # Verify user wrong password
        self.assertIsNone(self.db.verify_user("test_dev_agent", "IncorrectPass"))

        # 2. Create Project
        project_id = self.db.create_project("SAR Change Detection", "Synthetic Aperture Radar analysis workspace")
        self.assertIsNotNone(project_id)

        # 3. Create Conversation
        conv_id = self.db.create_conversation(user_id, "Bi-temporal Model Selection", project_id)
        self.assertIsNotNone(conv_id)
        
        # Check listing conversations
        conversations = self.db.list_conversations(user_id)
        self.assertEqual(len(conversations), 1)
        self.assertEqual(conversations[0]["conversation_id"], conv_id)
        self.assertEqual(conversations[0]["title"], "Bi-temporal Model Selection")
        self.assertEqual(conversations[0]["project_id"], project_id)

        # 4. Save and Retrieve Messages
        msg_user_id = self.db.save_message(conv_id, "user", "Which network works best for SAR?")
        msg_assistant_id = self.db.save_message(conv_id, "assistant", "SiamU-Net has proven robust for SAR bitemporal maps.")
        
        self.assertIsNotNone(msg_user_id)
        self.assertIsNotNone(msg_assistant_id)
        
        # Verify messages list in chronological order
        messages = self.db.get_messages(conv_id)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "user")
        self.assertEqual(messages[0]["content"], "Which network works best for SAR?")
        self.assertEqual(messages[1]["role"], "assistant")
        self.assertEqual(messages[1]["content"], "SiamU-Net has proven robust for SAR bitemporal maps.")

        # 5. Rolling Summaries
        self.db.save_summary(conv_id, "Initial selection centered on SiamU-Net configurations.")
        summary = self.db.get_summary(conv_id)
        self.assertEqual(summary, "Initial selection centered on SiamU-Net configurations.")
        
        # Update summary
        self.db.save_summary(conv_id, "Updated: Qwen proposed SiamU-Net configs for SAR.")
        updated_summary = self.db.get_summary(conv_id)
        self.assertEqual(updated_summary, "Updated: Qwen proposed SiamU-Net configs for SAR.")

        # 6. User Memory Profile Facts
        mem_id_1 = self.db.add_memory_fact(user_id, "User prefers PyTorch over TensorFlow.", "preference")
        mem_id_2 = self.db.add_memory_fact(user_id, "Hardware constraint matches 8GB RTX Laptop GPU.", "constraint")
        
        self.assertIsNotNone(mem_id_1)
        self.assertIsNotNone(mem_id_2)
        
        # Retrieve facts
        facts = self.db.get_memory_facts(user_id)
        self.assertEqual(len(facts), 2)
        self.assertEqual(facts[0]["fact"], "User prefers PyTorch over TensorFlow.")
        self.assertEqual(facts[0]["category"], "preference")
        self.assertEqual(facts[1]["fact"], "Hardware constraint matches 8GB RTX Laptop GPU.")
        self.assertEqual(facts[1]["category"], "constraint")
        
        # Delete specific memory fact
        self.db.delete_memory_fact(mem_id_1)
        remaining_facts = self.db.get_memory_facts(user_id)
        self.assertEqual(len(remaining_facts), 1)
        self.assertEqual(remaining_facts[0]["fact"], "Hardware constraint matches 8GB RTX Laptop GPU.")

        # 7. Rename Conversation
        self.db.rename_conversation(conv_id, "Bi-temporal SAR Models")
        conversations = self.db.list_conversations(user_id)
        self.assertEqual(conversations[0]["title"], "Bi-temporal SAR Models")

        # 8. Deletion & Cascading Cleanups
        self.db.delete_conversation(conv_id)
        conversations_after = self.db.list_conversations(user_id)
        self.assertEqual(len(conversations_after), 0)
        
        # Verify messages and summaries have been cleaned up automatically
        self.assertEqual(len(self.db.get_messages(conv_id)), 0)
        self.assertIsNone(self.db.get_summary(conv_id))


if __name__ == "__main__":
    unittest.main()
