import os
import sys
import unittest

# Adjust Python path to load backend modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import ChatDatabase
from retrieval.vector_db import PaperVectorDB
from schemas.canonical_paper import PaperDocument, PaperMetadata
from schemas.rag_schemas import PaperChunk


class TestLocalMemoryFlow(unittest.TestCase):
    def setUp(self):
        # Configure database instances pointing to mock test targets
        self.db = ChatDatabase(db_url="test-files")
        self.vector_db = PaperVectorDB()
        
        # Initialize test workspaces
        self.db.initialize_db()
        self.vector_db.initialize_db()

    def test_database_operations(self):
        user_id = "test_user_id"
        
        # 1. Register Mock User in JSON Database
        data = self.db._load_fallback()
        data["users"][user_id] = {
            "username": "tester",
            "password_hash": "dummy",
            "created_at": "2026-08-26"
        }
        self.db._save_fallback(data)
        
        # 2. Create conversation
        conv_id = self.db.create_conversation(user_id, "Test Dialogue Thread", "mock_pdf_path.pdf")
        self.assertIsNotNone(conv_id)
        self.assertTrue(conv_id.startswith("conv_"))
        
        # 3. Save message and load history transcripts
        msg_id = self.db.save_message(conv_id, "user", "How do I implement dynamic attention?")
        self.assertIsNotNone(msg_id)
        
        history = self.db.get_messages(conv_id)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["content"], "How do I implement dynamic attention?")
        
        # 4. Save and load summary
        self.db.save_summary(conv_id, "Rolling summary contents")
        summary = self.db.get_summary(conv_id)
        self.assertEqual(summary, "Rolling summary contents")
        
        # 5. List conversations
        conversations = self.db.list_conversations(user_id)
        self.assertTrue(any(c["conversation_id"] == conv_id for c in conversations))
        
        # 6. Save memory facts
        fact_id = self.db.add_memory_fact(user_id, "User prefers PyTorch Framework", "preference")
        self.assertIsNotNone(fact_id)
        
        facts = self.db.get_memory_facts(user_id)
        self.assertTrue(any("PyTorch Framework" in f["fact"] for f in facts))

        # Cleanup
        self.db.delete_conversation(conv_id)
        metadata = self.db.get_conversation(conv_id)
        self.assertIsNone(metadata)

    def test_vector_search_operations(self):
        # 1. Create a mock canonical paper document
        metadata = PaperMetadata(
            title="Swin Attention Networks",
            authors=["John Doe", "Jane Smith"],
            abstract="A custom spatial attention architecture.",
            sections_found=[],
            primary_contribution="A custom spatial attention architecture contribution."
        )
        doc = PaperDocument(
            paper_id="paper_swin_test",
            metadata=metadata,
            sections=[],
            tables=[],
            figures=[],
            equations=[]
        )
        
        # 2. Prepare mock chunks and mock embeddings (dimension size = 768)
        chunk1 = PaperChunk(
            chunk_id="chunk_1",
            paper_id="paper_swin_test",
            content="We introduce a spatial windowing shift attention backbone mechanism.",
            section="Methodology",
            page=3,
            content_type="text",
            source_id="sec_method"
        )
        chunk2 = PaperChunk(
            chunk_id="chunk_2",
            paper_id="paper_swin_test",
            content="Hyperparameters configuration: learning rate is 3e-4, optimizer is AdamW.",
            section="Experiments",
            page=5,
            content_type="text",
            source_id="sec_exp"
        )
        
        chunks = [chunk1, chunk2]
        
        # Fake vectors (one hot representation vectors)
        v1 = [0.0] * 768
        v1[0] = 1.0  # methodology query high weight
        
        v2 = [0.0] * 768
        v2[10] = 1.0  # parameters query high weight
        
        embeddings = [v1, v2]
        
        # 3. Save chunks inside local vector JSON cache
        self.vector_db.insert_paper_document(doc, chunks, embeddings)
        
        # 4. Perform keyword search
        kw_results = self.vector_db.keyword_search("optimizer configuration", top_k=2)
        self.assertTrue(len(kw_results) > 0)
        self.assertEqual(kw_results[0]["chunk_id"], "chunk_2")
        
        # 5. Perform semantic search (querying for Methodology chunk1)
        query_vector = [0.0] * 768
        query_vector[0] = 0.95  # close match to v1
        
        semantic_results = self.vector_db.semantic_search(query_vector, top_k=1)
        self.assertEqual(len(semantic_results), 1)
        self.assertEqual(semantic_results[0]["chunk_id"], "chunk_1")
        self.assertTrue(semantic_results[0]["similarity_score"] > 0.9)
        
        # 6. Perform hybrid search
        hybrid_results = self.vector_db.hybrid_search("optimizer", query_vector, top_k=2)
        self.assertEqual(len(hybrid_results), 2)
        
        # Check listing papers
        papers = self.vector_db.list_papers()
        self.assertTrue(any(p["paper_id"] == "paper_swin_test" for p in papers))


if __name__ == "__main__":
    unittest.main()
