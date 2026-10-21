"""
Verification tests for Phase 2: RAG Correctness & Data Isolation.
Verifies cross-paper retrieval isolation, complete indexing (no 5-chunk limit),
deduplication, deletion handling, explicit embedding failure, and contract compliance.
"""

import os
import shutil
import pytest
from unittest.mock import patch, MagicMock

from app.schemas.paper import PaperDocument, PaperMetadata, PaperSection
from app.retrieval.chunker import PaperChunk, chunk_paper_document
from app.retrieval.vector_db import PaperVectorDB
from app.retrieval.embeddings import (
    generate_local_embedding,
    generate_local_embeddings_batch,
    EmbeddingError
)
from app.tools.vector_search_tool import VectorSearchTool


@pytest.fixture
def temp_vector_db(tmp_path, monkeypatch):
    """Provides an isolated temporary directory for vector storage during testing."""
    test_storage = str(tmp_path / "rag_test_storage")
    os.makedirs(test_storage, exist_ok=True)
    monkeypatch.setattr("app.retrieval.vector_db.EMBEDDINGS_DIR", test_storage)
    vdb = PaperVectorDB()
    vdb.embeddings_dir = test_storage
    vdb.initialize_db()
    return vdb, test_storage


def test_cross_paper_retrieval_isolation(temp_vector_db):
    """
    CRITICAL TEST: Verify that querying Paper A NEVER retrieves chunks from Paper B,
    even when Paper B contains exact keyword matches.
    """
    vdb, storage_dir = temp_vector_db

    # Paper A: Vision Transformer
    paper_a = PaperDocument(
        paper_id="paper_vision_transformer",
        metadata=PaperMetadata(title="Vision Transformer", abstract="Transformers for images"),
        sections=[
            PaperSection(title="Architecture", content="PatchEmbed layer divides image into 16x16 visual tokens.")
        ]
    )
    chunks_a = [
        PaperChunk(chunk_id="a_1", paper_id="paper_vision_transformer", section="Architecture", content="PatchEmbed 16x16 tokens")
    ]
    vectors_a = [[0.9] + [0.0] * 767]
    vdb.insert_paper_document(paper_a, chunks_a, vectors_a)

    # Paper B: Diffusion Model
    paper_b = PaperDocument(
        paper_id="paper_diffusion_model",
        metadata=PaperMetadata(title="Diffusion Models", abstract="Denoising diffusion models"),
        sections=[
            PaperSection(title="Method", content="Denoising diffusion probabilistic model uses DDIM sampling scheduler.")
        ]
    )
    chunks_b = [
        PaperChunk(chunk_id="b_1", paper_id="paper_diffusion_model", section="Method", content="Denoising diffusion DDIM scheduler")
    ]
    vectors_b = [[0.0, 0.9] + [0.0] * 766]
    vdb.insert_paper_document(paper_b, chunks_b, vectors_b)

    # Query Paper A with terms that only exist in Paper B
    query_b_vector = [0.0, 0.9] + [0.0] * 766
    results_for_a = vdb.semantic_search(
        query_vector=query_b_vector,
        top_k=5,
        paper_id="paper_vision_transformer"
    )

    # All returned chunks must belong strictly to Paper A
    assert all(r["paper_id"] == "paper_vision_transformer" for r in results_for_a)
    assert not any(r["paper_id"] == "paper_diffusion_model" for r in results_for_a)

    # Query Paper B with terms from Paper A
    results_for_b = vdb.semantic_search(
        query_vector=[0.9] + [0.0] * 767,
        top_k=5,
        paper_id="paper_diffusion_model"
    )
    assert all(r["paper_id"] == "paper_diffusion_model" for r in results_for_b)
    assert not any(r["paper_id"] == "paper_vision_transformer" for r in results_for_b)


def test_complete_indexing_no_truncation(temp_vector_db):
    """
    Verify that all chunks of a paper are indexed and retrievable,
    verifying elimination of the chunks[:5] truncation limit.
    """
    vdb, _ = temp_vector_db

    # Create a paper with 12 distinct sections
    sections = [
        PaperSection(title=f"Section_{i}", content=f"Content for section {i} detailing algorithmic steps.")
        for i in range(12)
    ]
    doc = PaperDocument(
        paper_id="full_indexing_paper",
        metadata=PaperMetadata(title="Multi-Section Paper", abstract="Extensive paper"),
        sections=sections
    )

    chunks = chunk_paper_document(doc, chunk_size=50)
    assert len(chunks) >= 12, "Document should produce at least 12 chunks"

    embeddings = [[0.1 * (i % 5)] + [0.0] * 767 for i in range(len(chunks))]
    res = vdb.insert_paper_document(doc, chunks, embeddings)

    assert res["chunks_stored"] == len(chunks)
    assert res["chunks_stored"] > 5, "Must index more than 5 chunks"

    # Verify all chunks exist in stored metadata
    paper_meta = vdb.get_paper("full_indexing_paper")
    assert paper_meta["chunk_count"] == len(chunks)


def test_chunk_deduplication(temp_vector_db):
    """Verify that duplicate chunks are detected and deduplicated via content hashing."""
    vdb, _ = temp_vector_db

    doc = PaperDocument(
        paper_id="dedup_paper",
        metadata=PaperMetadata(title="Dedup Test"),
        sections=[PaperSection(title="Abstract", content="Duplicated text block.")]
    )

    identical_chunks = [
        PaperChunk(chunk_id="chk_1", paper_id="dedup_paper", section="Abstract", content="Duplicated text block."),
        PaperChunk(chunk_id="chk_2", paper_id="dedup_paper", section="Abstract", content="Duplicated text block."),
        PaperChunk(chunk_id="chk_3", paper_id="dedup_paper", section="Unique", content="Unique text block.")
    ]
    vectors = [[0.1] * 768, [0.1] * 768, [0.2] * 768]

    res = vdb.insert_paper_document(doc, identical_chunks, vectors)
    assert res["chunks_stored"] == 2, "Expected 1 duplicate chunk to be skipped"
    assert res["deduplicated"] == 1


def test_paper_deletion(temp_vector_db):
    """Verify that deleting a paper cleans up its vector cache completely."""
    vdb, storage_dir = temp_vector_db

    doc = PaperDocument(
        paper_id="paper_to_delete",
        metadata=PaperMetadata(title="Temporary Paper"),
        sections=[PaperSection(title="Intro", content="Temporary contents.")]
    )
    vdb.insert_paper_document(
        doc,
        [PaperChunk(chunk_id="del_1", paper_id="paper_to_delete", section="Intro", content="Temporary contents.")],
        [[0.5] * 768]
    )

    json_path = os.path.join(storage_dir, "paper_to_delete.json")
    assert os.path.exists(json_path)

    deleted = vdb.delete_paper("paper_to_delete")
    assert deleted is True
    assert not os.path.exists(json_path)

    # Retrieval should now return empty
    res = vdb.semantic_search([0.5] * 768, paper_id="paper_to_delete")
    assert len(res) == 0


def test_embedding_error_propagation_no_pseudo_vectors():
    """
    Verify that when embedding service fails, it raises EmbeddingError
    instead of producing silent ord(char) character vectors.
    """
    with patch("ollama.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.embeddings.side_effect = ConnectionError("Ollama daemon unreachable")
        mock_client_cls.return_value = mock_client

        with pytest.raises(EmbeddingError) as exc_info:
            generate_local_embedding("Sample query", max_retries=1, retry_delay=0.01)

        assert "Embedding generation failed" in str(exc_info.value)


def test_standard_rag_retrieval_contract(temp_vector_db):
    """Verify that retrieval results adhere to the standardized RAG contract."""
    vdb, _ = temp_vector_db

    doc = PaperDocument(
        paper_id="contract_paper",
        metadata=PaperMetadata(title="Contract Paper"),
        sections=[PaperSection(title="Method", content="Detailed architecture formulation.")]
    )
    chunks = [
        PaperChunk(chunk_id="chk_c1", paper_id="contract_paper", section="Method", content="Detailed architecture formulation.")
    ]
    vectors = [[0.8] + [0.0] * 767]
    vdb.insert_paper_document(doc, chunks, vectors)

    results = vdb.hybrid_search(
        query_text="architecture",
        query_vector=[0.8] + [0.0] * 767,
        paper_id="contract_paper",
        top_k=1
    )

    assert len(results) == 1
    hit = results[0]

    # Required contract keys
    required_keys = ["paper_id", "chunk_id", "text", "section", "page", "score"]
    for key in required_keys:
        assert key in hit, f"Missing required contract key '{key}' in retrieval result: {hit}"

    assert hit["paper_id"] == "contract_paper"
    assert hit["chunk_id"] == "chk_c1"
    assert "Detailed architecture" in hit["text"]
    assert isinstance(hit["score"], float)


def test_vector_search_tool_isolation(temp_vector_db):
    """Verify VectorSearchTool respects paper_id without cross-paper fallback."""
    vdb, _ = temp_vector_db

    doc_a = PaperDocument(
        paper_id="tool_paper_a",
        metadata=PaperMetadata(title="Paper A"),
        sections=[PaperSection(title="Intro", content="Specific vision transformer details.")]
    )
    vdb.insert_paper_document(
        doc_a,
        [PaperChunk(chunk_id="ta_1", paper_id="tool_paper_a", section="Intro", content="Specific vision transformer details.")],
        [[0.9] + [0.0] * 767]
    )

    tool = VectorSearchTool()
    # Search for Paper B (which does not exist)
    out = tool.execute(query="transformer", paper_id="non_existent_paper_b")
    assert "No matching paper chunks found in paper 'non_existent_paper_b'" in out
    assert "tool_paper_a" not in out, "Tool must not fall back to other papers"
