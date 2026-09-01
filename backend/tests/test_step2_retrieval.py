import sys
import os
import tempfile
import pytest

# Add new_backend to python search path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from app.extraction.pdf_parser import parse_pdf_document
from app.retrieval.chunker import chunk_paper_document
from app.retrieval.embeddings import generate_local_embedding
from app.retrieval.vector_db import PaperVectorDB

workspace_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sample_pdf_path = os.path.join(workspace_dir, "[2].pdf")
if not os.path.exists(sample_pdf_path):
    sample_pdf_path = os.path.join(workspace_dir, "backend", "storage", "papers", "2.pdf")
if not os.path.exists(sample_pdf_path):
    sample_pdf_path = os.path.join(workspace_dir, "backend", "storage", "papers", "[2].pdf")


def test_pdf_parsing_and_vector_indexing():
    print(f"\n--- Testing Step 2 Retrieval Engine with PDF: '{sample_pdf_path}' ---")
    if not os.path.exists(sample_pdf_path):
        pytest.skip(f"Sample PDF '[2].pdf' not present for test at {sample_pdf_path}")
    
    # 1. Parse PDF to canonical PaperDocument
    paper_doc = parse_pdf_document(sample_pdf_path)
    print(f"Parsed Paper ID: '{paper_doc.paper_id}'")
    print(f"Title: '{paper_doc.metadata.title}'")
    print(f"Sections extracted: {len(paper_doc.sections)}")
    assert paper_doc.paper_id == "2" or len(paper_doc.paper_id) > 0
    assert len(paper_doc.sections) > 0

    # 2. Chunk Paper Document
    chunks = chunk_paper_document(paper_doc, chunk_size=300)
    print(f"Generated {len(chunks)} layout chunks.")
    assert len(chunks) > 0

    # 3. Generate Local Embeddings
    print("Generating local embeddings for first 3 chunks...")
    embeddings = [generate_local_embedding(c.content) for c in chunks[:3]]
    assert len(embeddings) == 3
    assert len(embeddings[0]) in [384, 768]

    # 4. Insert into Vector Database
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = os.path.join(tmp_dir, "test_vector_db.json")
        vdb = PaperVectorDB(db_file=db_path)
        vdb.initialize_db()
        vdb.insert_paper_document(paper_doc, chunks[:3], embeddings)

        # 5. Test Hybrid Vector Search
        query = "deep learning model architecture"
        q_vec = generate_local_embedding(query)
        results = vdb.hybrid_search(query, q_vec, top_k=2)
        print(f"Search query: '{query}' -> Returned {len(results)} matches.")
        assert len(results) > 0
        assert "score" in results[0]

    print("\nAll Step 2 Retrieval & Vector Engine tests passed successfully!")


if __name__ == "__main__":
    test_pdf_parsing_and_vector_indexing()
