import pytest
from app.extraction.merger import extract_consensus_tables, _resolve_page_bounds, merge_extractions
from app.schemas.canonical_paper import PaperDocument


def test_extract_consensus_tables_preserves_unique_tables():
    """Verify that distinct tables from Docling, Gemini, and PyMuPDF are all preserved."""
    docling_out = {
        "tables": [
            {"caption": "Table 1: Baseline Architecture", "content_markdown": "| Layer | Dim |\n|---|---|\n| Conv | 64 |", "page": 2}
        ]
    }
    gemini_out = {
        "tables": [
            {"caption": "Table 2: Ablation Study", "content_markdown": "| Method | Acc |\n|---|---|\n| Ours | 94.2 |", "page": 4}
        ]
    }
    pymupdf_out = {
        "sections": {
            "Tables": {
                "subsections": {
                    "Table 3: Hyperparameters": "| Param | Value |\n|---|---|\n| lr | 0.001 |"
                }
            }
        }
    }

    tables = extract_consensus_tables(
        docling_out=docling_out,
        pymupdf_out=pymupdf_out,
        gemini_out=gemini_out
    )

    assert len(tables) == 3
    captions = [t.caption for t in tables]
    assert any("Table 1" in c for c in captions)
    assert any("Table 2" in c for c in captions)
    assert any("Table 3" in c for c in captions)


def test_extract_consensus_tables_merges_overlapping():
    """Verify that same table from Docling and Gemini merges and chooses richest markdown."""
    docling_out = {
        "tables": [
            {"caption": "Table 1", "content_markdown": "Short text", "page": 1}
        ]
    }
    gemini_out = {
        "tables": [
            {"caption": "Table 1: Benchmark Comparisons", "content_markdown": "| Model | F1 |\n|---|---|\n| Proposed | 0.98 |", "page": 3}
        ]
    }

    tables = extract_consensus_tables(docling_out=docling_out, gemini_out=gemini_out)
    assert len(tables) == 1
    t = tables[0]
    assert "Benchmark Comparisons" in t.caption
    assert "| Model | F1 |" in t.content_markdown
    assert t.page == 3


def test_resolve_page_bounds_from_pymupdf_metadata():
    """Verify _resolve_page_bounds looks up actual page start/end from PyMuPDF layout metadata."""
    routed_data = {
        "inspector_report": {"pages": 10},
        "pymupdf_output": {
            "sections": {
                "1. Introduction": {"page_start": 1, "page_end": 2},
                "3. Methodology": {"page_start": 3, "page_end": 5},
                "4. Experimental Results": {"page_start": 6, "page_end": 8}
            }
        }
    }

    p_start, p_end = _resolve_page_bounds("3. Methodology", routed_data)
    assert p_start == 3
    assert p_end == 5

    # Normalized matching
    p_start2, p_end2 = _resolve_page_bounds("Methodology", routed_data)
    assert p_start2 == 3
    assert p_end2 == 5

    # Section spanning to page 8
    p_start3, p_end3 = _resolve_page_bounds("Experimental Results", routed_data)
    assert p_start3 == 6
    assert p_end3 == 8


def test_merge_extractions_full():
    """Verify full extraction pipeline merging produces valid PaperDocument with resolved coordinates."""
    routed_data = {
        "paper_id": "test_paper_123",
        "filename": "test_paper.pdf",
        "inspector_report": {"pages": 6, "text_coverage_chars": 15000},
        "gemini_output": {
            "valid": True,
            "title": "Attention Is All You Need",
            "authors": ["Vaswani et al."],
            "abstract": "We propose the Transformer.",
            "sections": {
                "1. Introduction": {"content": "Recurrent neural networks..."},
                "2. Model Architecture": {"content": "The Transformer follows an encoder-decoder architecture."}
            }
        },
        "pymupdf_output": {
            "sections": {
                "1. Introduction": {"content": "Recurrent...", "page_start": 1, "page_end": 2},
                "2. Model Architecture": {"content": "The Transformer...", "page_start": 2, "page_end": 4}
            }
        },
        "docling_output": {
            "tables": [
                {"caption": "Table 1: Maximum path lengths", "content_markdown": "| Layer | Complexity |\n|---|---|\n| Self-Attn | O(1) |", "page": 4}
            ]
        }
    }

    doc = merge_extractions(routed_data)
    assert isinstance(doc, PaperDocument)
    assert doc.metadata.title == "Attention Is All You Need"
    assert len(doc.sections) == 2
    # Check resolved page bounds
    sec1 = [s for s in doc.sections if "Introduction" in s.title][0]
    assert sec1.page_start == 1
    assert sec1.page_end == 2
    sec2 = [s for s in doc.sections if "Model Architecture" in s.title][0]
    assert sec2.page_start == 2
    assert sec2.page_end == 4
    # Check tables
    assert len(doc.tables) == 1
    assert "Table 1" in doc.tables[0].caption
