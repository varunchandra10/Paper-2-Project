import sys
import os
import pytest

# Add new_backend to python search path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from app.evals.eval_suite import (
    eval_extraction_accuracy,
    eval_grounding_citations,
    eval_rag_relevance,
    run_reliability_benchmark
)


def test_extraction_accuracy():
    res = eval_extraction_accuracy("test_paper_01")
    assert "score" in res
    assert res["score"] >= 0.0


def test_grounding_citations():
    res = eval_grounding_citations("test_paper_01")
    assert "score" in res
    assert res["score"] == 95.0


def test_rag_relevance():
    res = eval_rag_relevance("test_paper_01")
    assert "score" in res
    assert res["score"] == 92.5


def test_reliability_benchmark():
    report = run_reliability_benchmark("test_paper_01")
    assert "reliability_score" in report
    assert "verdict" in report
    assert report["reliability_score"] >= 75.0
    assert report["verdict"] == "PRODUCTION_READY"


if __name__ == "__main__":
    print("Running Step 6 Evals Benchmark tests...")
    test_extraction_accuracy()
    test_grounding_citations()
    test_rag_relevance()
    test_reliability_benchmark()
    print("All Step 6 Evals Benchmark tests passed successfully!")
