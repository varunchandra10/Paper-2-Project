"""
Tests for Phase 14: Cost & Resource Optimization.

Verifies:
1. Token measurement and cost calculation accuracy.
2. Duplicate call detection.
3. Prompt completion caching.
4. Unchanged paper reprocessing avoidance via SHA-256 caching.
5. Batch embedding chunk deduplication.
6. Single Model vs Dual Model Tournament contract & experiment validity.
"""

import os
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.core.cost_optimizer import cost_optimizer, CostAndResourceOptimizer, MODEL_PRICING
from app.schemas.paper import PaperDocument, PaperMetadata, PaperSection
from app.retrieval.embeddings import generate_local_embeddings_batch
from app.graph.nodes.ingestion import ingestion_node
from app.evals.benchmarks.cost_optimization_benchmark import (
    CodeEvaluator,
    BENCHMARK_TASKS,
    REPRESENTATIVE_CODE
)


def test_token_estimation_and_cost_calculation():
    """Verifies token estimation and multi-provider pricing calculations."""
    text = "def attention(q, k, v):\n    return torch.matmul(q, k.T)\n"
    tok = cost_optimizer.estimate_tokens(text)
    assert tok > 5
    assert tok < 25

    # Pricing checks
    # Local models: $0.00
    cost_local = cost_optimizer.calculate_cost("qwen2.5:7b", 10000, 5000)
    assert cost_local == 0.0

    # Gemini: $0.15 input / $0.60 output per 1M tokens
    # 1M in = $0.15, 1M out = $0.60
    cost_gemini = cost_optimizer.calculate_cost("gemini-2.0-flash", 1_000_000, 1_000_000)
    assert abs(cost_gemini - 0.75) < 1e-4

    # HF Coder: $0.20 input / $0.20 output per 1M tokens
    cost_hf = cost_optimizer.calculate_cost("Qwen/Qwen2.5-Coder-32B-Instruct", 1_000_000, 1_000_000)
    assert abs(cost_hf - 0.40) < 1e-4


def test_duplicate_call_detection(tmp_path):
    """Verifies that identical model queries are flagged as duplicate calls."""
    opt = CostAndResourceOptimizer(
        cache_dir=str(tmp_path / "paper_cache"),
        prompt_cache_dir=str(tmp_path / "prompt_cache")
    )

    res1 = opt.record_call(
        stage="extraction",
        model_name="gemini-2.0-flash",
        prompt="Extract learning rate from section 3",
        completion="0.001",
        duration_ms=450.0
    )
    assert res1["is_duplicate"] is False
    assert opt.duplicate_calls_detected == 0

    # Duplicate call with exact same prompt and model
    res2 = opt.record_call(
        stage="extraction",
        model_name="gemini-2.0-flash",
        prompt="Extract learning rate from section 3",
        completion="0.001",
        duration_ms=420.0
    )
    assert res2["is_duplicate"] is True
    assert opt.duplicate_calls_detected == 1


def test_prompt_completion_caching(tmp_path):
    """Verifies fast retrieval of cached completions and resource savings."""
    opt = CostAndResourceOptimizer(
        cache_dir=str(tmp_path / "paper_cache"),
        prompt_cache_dir=str(tmp_path / "prompt_cache")
    )

    model = "gemini-2.0-flash"
    prompt = "Explain residual connections in 1 sentence."
    completion = "Residual connections add the identity input to the output of nonlinear transformations."

    # Cache miss initially
    assert opt.get_cached_completion(model, prompt) is None

    # Populate cache
    opt.set_cached_completion(model, prompt, completion, latency_ms=850.0)

    # Cache hit
    cached_text = opt.get_cached_completion(model, prompt)
    assert cached_text == completion
    assert opt.saved_tokens > 0
    assert opt.saved_latency_ms == 850.0


def test_unchanged_paper_ingestion_caching(tmp_path, monkeypatch):
    """
    Verifies that identical PDFs are recognized via SHA-256,
    bypassing parsing, embedding, and LLM calls.
    """
    vdb_dir = tmp_path / "rag_based"
    vdb_dir.mkdir(parents=True, exist_ok=True)
    paper_cache_dir = tmp_path / "paper_cache"
    paper_cache_dir.mkdir(parents=True, exist_ok=True)

    opt = CostAndResourceOptimizer(cache_dir=str(paper_cache_dir))
    monkeypatch.setattr("app.core.cost_optimizer.cost_optimizer", opt)

    test_doc = PaperDocument(
        paper_id="paper_dedup_test",
        metadata=PaperMetadata(title="Deduplication Benchmark Paper", abstract="An empirical paper on efficiency."),
        sections=[PaperSection(title="Introduction", content="Sample content text for hashing.")]
    )
    pdf_hash = "abc1234567890deadbeef45678901234567890deadbeef"

    # 1. Before caching: cache returns None
    assert opt.get_cached_paper_ingestion(pdf_hash) is None

    # 2. Simulate vector store file existence
    vdb_file = vdb_dir / f"{test_doc.paper_id}.json"
    vdb_file.write_text(json.dumps({"chunks": []}), encoding="utf-8")
    monkeypatch.setattr("app.core.config.settings.STORAGE_DIR", str(tmp_path))
    monkeypatch.setattr("app.core.config.settings.RAG_EMBEDDINGS_DIR", str(vdb_dir))

    # 3. Cache the paper
    opt.cache_paper_ingestion(
        pdf_hash=pdf_hash,
        paper_doc=test_doc,
        raw_sections={"Introduction": "Sample content text for hashing."},
        metadata={"title": test_doc.metadata.title},
        estimated_tokens_saved=5000,
        estimated_latency_ms=2500.0
    )

    # 4. Verify retrieval
    cached = opt.get_cached_paper_ingestion(pdf_hash)
    assert cached is not None
    assert cached["paper_doc"].paper_id == "paper_dedup_test"
    assert cached["paper_doc"].metadata.title == "Deduplication Benchmark Paper"
    assert opt.saved_tokens >= 5000
    assert opt.saved_latency_ms >= 2500.0


def test_ingestion_node_avoids_reprocessing_unchanged_papers(tmp_path, monkeypatch):
    """Verifies ingestion_node returns early with cache_hit=True on duplicate paper submission."""
    test_pdf = tmp_path / "sample_paper.pdf"
    test_pdf.write_bytes(b"%PDF-1.4 simulated pdf document content for hash test" * 20)

    from app.core.manifest import compute_file_sha256
    pdf_hash = compute_file_sha256(str(test_pdf))

    test_doc = PaperDocument(
        paper_id="paper_ingest_cache_test",
        metadata=PaperMetadata(title="Cached Ingestion Paper"),
        sections=[PaperSection(title="Methods", content="Cached methodology.")]
    )

    vdb_dir = tmp_path / "rag_based"
    vdb_dir.mkdir(parents=True, exist_ok=True)
    vdb_file = vdb_dir / f"{test_doc.paper_id}.json"
    vdb_file.write_text(json.dumps({"chunks": []}), encoding="utf-8")

    monkeypatch.setattr("app.core.config.settings.STORAGE_DIR", str(tmp_path))
    monkeypatch.setattr("app.core.config.settings.RAG_EMBEDDINGS_DIR", str(vdb_dir))

    # Pre-cache paper ingestion
    cost_optimizer.cache_dir = str(tmp_path / "paper_cache")
    os.makedirs(cost_optimizer.cache_dir, exist_ok=True)
    cost_optimizer.cache_paper_ingestion(
        pdf_hash=pdf_hash,
        paper_doc=test_doc,
        raw_sections={"Methods": "Cached methodology."},
        metadata={"domain": "AI"}
    )

    # Execute ingestion_node
    res = ingestion_node({"pdf_path": str(test_pdf)})
    assert res.get("cache_hit") is True
    assert res["paper_doc"].paper_id == "paper_ingest_cache_test"


def test_batch_embedding_chunk_deduplication():
    """Verifies that generate_local_embeddings_batch caches repeated chunk hashes."""
    texts = [
        "Identical repeated header in paper",
        "Unique chunk 1 describing methodology",
        "Identical repeated header in paper",  # Repeated
        "Unique chunk 2 describing ablation results"
    ]

    with patch("app.retrieval.embeddings.generate_local_embedding") as mock_emb:
        mock_emb.return_value = [0.1] * 768
        embs = generate_local_embeddings_batch(texts)

        assert len(embs) == 4
        # Even though 4 chunks were requested, the identical chunk should be retrieved from cache
        # Total calls to generate_local_embedding <= 3
        assert mock_emb.call_count <= 3


def test_single_model_vs_dual_tournament_evaluator():
    """Verifies CodeEvaluator metrics on syntax-valid vs syntax-broken code."""
    evaluator = CodeEvaluator()

    valid_code = REPRESENTATIVE_CODE["task_1_cross_attention"]["candidate_a"]
    faulty_code = REPRESENTATIVE_CODE["task_1_cross_attention"]["faulty_candidate"]

    # 1. AST Pass
    ast_valid, err_valid = evaluator.evaluate_ast(valid_code)
    ast_faulty, err_faulty = evaluator.evaluate_ast(faulty_code)
    assert ast_valid is True
    assert ast_faulty is False
    assert "SyntaxError" in err_faulty

    # 2. Compile Pass
    comp_valid, _ = evaluator.evaluate_compile(valid_code)
    comp_faulty, _ = evaluator.evaluate_compile(faulty_code)
    assert comp_valid is True
    assert comp_faulty is False

    # 3. Runtime & Functional Pass
    run_ok, _, instance = evaluator.evaluate_runtime(valid_code)
    assert run_ok is True
    assert instance is not None

    func_ok, _ = evaluator.evaluate_functional(instance)
    assert func_ok is True

    # 4. Paper Fidelity
    fid_score = evaluator.evaluate_paper_fidelity(valid_code, ["sqrt", "softmax", "matmul", "Linear", "forward"])
    assert fid_score == 100.0


def test_cost_optimizer_report_structure():
    """Verifies comprehensive optimization metrics report structure."""
    rep = cost_optimizer.get_optimization_report()
    assert "total_invocations" in rep
    assert "duplicate_calls_detected" in rep
    assert "tokens" in rep
    assert "costs_usd" in rep
    assert "latency" in rep
    assert "model_pricing_reference" in rep
