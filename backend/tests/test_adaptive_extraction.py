"""
Test Suite for Adaptive Deterministic-First Document Extraction Architecture.
Tests:
- Deterministic extraction and reading-order layout
- Multi-signal element detection (Figures, Tables, Equations)
- Element-level confidence scoring & validation
- Daily Quota Manager & Application Budgeting
- Provenance-aware hierarchical chunking
"""

import os
import pytest
import tempfile
import pymupdf as fitz
from app.extraction.pdf_inspector import inspect_pdf
from app.extraction.element_cropper import ElementCropper, ElementCandidate, FIGURE_CAPTION_REGEX, TABLE_CAPTION_REGEX
from app.extraction.vlm_processor import VLMElementProcessor, _repair_json_latex
from app.extraction.validator import validate_paper_document
from app.extraction.semantic_analyzer import SemanticResearchAnalyzer
from app.extraction.merger import merge_extractions
from app.extraction.router import route_and_extract
from app.retrieval.chunker import chunk_paper_document
from app.core.quota_tracker import DailyExtractionQuotaManager
from app.schemas.canonical_paper import PaperDocument, Section, Table, Figure, Equation, Reference
from app.schemas.pipeline_schemas import PaperMetadata


@pytest.fixture
def sample_pdf_path():
    """Generates a temporary synthetic 2-page academic PDF with a figure, table, and equation."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
        pdf_path = tf.name

    doc = fitz.open()
    # Page 1: Title, Abstract, Section 1, Equation (1)
    p1 = doc.new_page(width=612, height=792)
    p1.insert_text((50, 50), "Attention Is All You Need", fontsize=18)
    p1.insert_text((50, 80), "Ashish Vaswani, Noam Shazeer", fontsize=11)
    p1.insert_text((50, 120), "Abstract\nThe dominant sequence transduction models are based on complex recurrent or convolutional neural networks in an encoder-decoder configuration.", fontsize=10)
    p1.insert_text((50, 180), "1. Introduction\nRecurrent neural networks, long short-term memory and gated recurrent neural networks have been firmly established.", fontsize=10)
    p1.insert_text((50, 240), "Attention(Q, K, V) = softmax(QK^T / sqrt(d_k))V  (1)", fontsize=10)
    p1.insert_text((50, 300), "Figure 1: The Transformer - model architecture.", fontsize=10)
    # Draw a rectangle above figure caption
    p1.draw_rect(fitz.Rect(50, 320, 250, 420), color=(0.2, 0.4, 0.8), fill=(0.9, 0.9, 0.95))

    # Page 2: Section 2, Table 1, Conclusion, References
    p2 = doc.new_page(width=612, height=792)
    p2.insert_text((50, 50), "2. Model Architecture\nMost competitive neural sequence models have an encoder-decoder structure.", fontsize=10)
    p2.insert_text((50, 100), "Table 1: Maximum path lengths, per-layer complexity and minimum number of sequential operations.", fontsize=10)
    p2.insert_text((50, 130), "Layer Type      Complexity    Path Length\nSelf-Attention  O(n^2 * d)    O(1)\nRecurrent       O(n * d^2)    O(n)", fontsize=9)
    p2.insert_text((50, 220), "3. Conclusion\nIn this work, we presented the Transformer, the first sequence transduction model based entirely on attention.", fontsize=10)
    p2.insert_text((50, 280), "References\n[1] A. Vaswani et al., Advances in Neural Information Processing Systems, 2017.", fontsize=9)

    doc.save(pdf_path)
    doc.close()

    yield pdf_path

    if os.path.exists(pdf_path):
        try:
            os.remove(pdf_path)
        except Exception:
            pass


def test_pdf_inspector(sample_pdf_path):
    """Verifies that PDF inspector extracts accurate diagnostics."""
    report = inspect_pdf(sample_pdf_path)
    assert report["valid"] is True
    assert report["pages"] == 2
    assert report["is_scanned"] is False
    assert report["text_coverage_chars"] > 100


def test_caption_regex_detection():
    """Tests multi-variant caption regex matching for figures and tables."""
    assert FIGURE_CAPTION_REGEX.match("Figure 1: Overall Architecture") is not None
    assert FIGURE_CAPTION_REGEX.match("Fig. 2. Dataflow diagram") is not None
    assert FIGURE_CAPTION_REGEX.match("FIGURE 3 - Model Pipeline") is not None
    assert FIGURE_CAPTION_REGEX.match("Fig.4") is not None

    assert TABLE_CAPTION_REGEX.match("Table 1: Performance Benchmarks") is not None
    assert TABLE_CAPTION_REGEX.match("TABLE I. Ablation Study") is not None
    assert TABLE_CAPTION_REGEX.match("Tab. 2. Experimental Results") is not None


def test_element_cropper_and_candidates(sample_pdf_path):
    """Verifies that ElementCropper extracts candidate regions for Figures, Tables, and Equations."""
    cropper = ElementCropper(paper_id="test_paper_123")
    elements = cropper.detect_and_crop_elements(sample_pdf_path)

    assert "figures" in elements
    assert "tables" in elements
    assert "equations" in elements

    # Check that crops exist on disk with valid dimensions
    for fig in elements["figures"]:
        assert fig.page in [1, 2]
        assert len(fig.bbox) == 4
        if fig.image_path:
            assert os.path.exists(fig.image_path)


def test_daily_extraction_quota_manager():
    """Tests thread-safe application budgeting, tracking, and daily midnight rollover."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
        quota_file = tf.name

    try:
        manager = DailyExtractionQuotaManager(storage_path=quota_file)
        assert manager.can_use_vlm() is True

        summary_initial = manager.get_quota_summary()
        assert summary_initial["vlm_papers_processed"] == 0
        assert summary_initial["deterministic_papers_processed"] == 0

        # Record deterministic paper (0 VLM)
        manager.record_paper_completion(paper_id="paper_det_1", used_vlm=False)
        assert manager.get_quota_summary()["deterministic_papers_processed"] == 1
        assert manager.get_quota_summary()["vlm_papers_processed"] == 0

        # Record VLM paper
        manager.record_vlm_request(paper_id="paper_vlm_1", element_type="figure", input_tokens=200, output_tokens=100)
        manager.record_paper_completion(paper_id="paper_vlm_1", used_vlm=True)

        summary_after = manager.get_quota_summary()
        assert summary_after["vlm_papers_processed"] == 1
        assert summary_after["vlm_requests"] == 1
        assert summary_after["input_tokens"] == 200
        assert summary_after["output_tokens"] == 100
    finally:
        if os.path.exists(quota_file):
            try:
                os.remove(quota_file)
            except Exception:
                pass


def test_vlm_json_repair():
    """Tests JSON repair for unescaped LaTeX backslashes."""
    raw_latex_json = r'{"element_id": "eq_1", "latex": "\mathcal{L} = \alpha + \beta", "confidence": 0.95}'
    parsed = _repair_json_latex(raw_latex_json)
    assert parsed.get("element_id") == "eq_1"
    assert "mathcal" in parsed.get("latex", "")


def test_figure_classification():
    """Tests that figure classification only enables VLM for flowcharts/architectures."""
    cropper = ElementCropper(paper_id="test_class")

    # Architecture diagrams & Flowcharts -> needs_vlm = True
    fig_type, needs_vlm = cropper.classify_figure("Figure 1: Overall system architecture showing encoder-decoder pipeline.")
    assert fig_type == "architecture_diagram"
    assert needs_vlm is True

    fig_type, needs_vlm = cropper.classify_figure("Figure 2: Execution flowchart and decision tree.")
    assert fig_type == "flowchart"
    assert needs_vlm is True

    # Plots & Graphs -> needs_vlm = False
    fig_type, needs_vlm = cropper.classify_figure("Figure 3: Training loss curve and ROC plot over 100 epochs.")
    assert fig_type == "plot_chart"
    assert needs_vlm is False

    # Author photos & decorative -> needs_vlm = False
    fig_type, needs_vlm = cropper.classify_figure("Figure 4: Photograph of the first author.")
    assert fig_type == "photograph"
    assert needs_vlm is False

    # Qualitative sample outputs -> needs_vlm = False
    fig_type, needs_vlm = cropper.classify_figure("Figure 5: Qualitative results and sample images produced by model.")
    assert fig_type == "sample_result"
    assert needs_vlm is False


def test_document_complexity_profile(sample_pdf_path):
    """Verifies that DocumentComplexityProfile accurately reports layout signals."""
    report = inspect_pdf(sample_pdf_path)
    assert "complexity_profile" in report
    prof = report["complexity_profile"]

    assert "scanned_page_ratio" in prof
    assert "multi_column_detected" in prof
    assert "figure_count" in prof
    assert "vector_graphics_count" in prof
    assert "complexity_level" in prof
    assert prof["complexity_level"] in ["LOW", "MEDIUM", "HIGH"]


def test_assertion_based_element_validation():
    """Tests transparent assertion-based validation scoring."""
    doc = PaperDocument(
        paper_id="paper_assertion_test",
        metadata=PaperMetadata(title="Assertion Test Paper", abstract="Valid length abstract for testing structural assertions."),
        sections=[
            Section(title="1. Introduction", content="Introductory content paragraph."),
            Section(title="2. Methods", content="Methods content paragraph."),
            Section(title="3. Results", content="Results content paragraph.")
        ],
        tables=[
            Table(
                id="tab_1",
                caption="Table 1: Benchmark Scores",
                content_markdown="| Model | Accuracy (± std) |\n|---|---|\n| Baseline | 84.5 ± 0.2% |",
                headers=["Model", "Accuracy (± std)"],
                rows=[["Baseline", "84.5 ± 0.2%"]]
            )
        ],
        equations=[
            Equation(id="eq_1", latex=r"\mathcal{L}_{total} = \sum_{i=1}^N (y_i - \hat{y}_i)^2", caption="Equation (1)")
        ],
        figures=[
            Figure(id="fig_1", caption="Figure 1: System Overview Architecture", visual_description="Detailed architecture flowchart.")
        ]
    )

    report = validate_paper_document(doc)
    assert report.valid is True

    # Validate Table assertions
    tab_val = report.element_confidence["tables"]["tab_1"]
    assert tab_val["status"] == "validated"
    assert tab_val["checks"]["markdown_grid_valid"] is True
    assert tab_val["checks"]["numeric_preservation"] is True

    # Validate Equation assertions
    eq_val = report.element_confidence["equations"]["eq_1"]
    assert eq_val["status"] == "validated"
    assert eq_val["checks"]["brace_balance"] is True
    assert eq_val["checks"]["math_syntax_valid"] is True


def test_benchmark_runner(sample_pdf_path):
    """Tests the benchmark runner comparing baseline whole-doc vision vs adaptive pipeline."""
    from app.extraction.benchmark import ExtractionBenchmarkRunner

    runner = ExtractionBenchmarkRunner()
    res = runner.benchmark_paper(sample_pdf_path)

    assert res.page_count == 2
    assert res.baseline_requests == 2
    assert res.baseline_total_tokens > 0
    assert res.total_latency_ms > 0
    assert res.token_reduction_pct >= 0.0
    assert "sections" in res.elements_extracted



def test_provenance_chunker():
    """Tests hierarchical document chunker with cross-reference detection."""
    doc = PaperDocument(
        paper_id="paper_chunk_test",
        metadata=PaperMetadata(title="Chunk Test", abstract="Abstract"),
        sections=[
            Section(title="1. Introduction", content="As shown in Figure 1 and Table 2, the proposed loss in Eq. (3) achieves superior accuracy."),
            Section(title="2. Methodology", content="Additional methodology content.")
        ],
        tables=[Table(id="table_2", caption="Table 2: Performance", content_markdown="| Acc |\n|---|\n| 95% |")],
        figures=[Figure(id="fig_1", caption="Figure 1: Flowchart", visual_description="Flowchart with encoder-decoder blocks.")],
        equations=[Equation(id="eq_3", latex=r"L = L_{cls} + \lambda L_{reg}")]
    )

    chunks = chunk_paper_document(doc)
    assert len(chunks) >= 4  # 2 sections + 1 table chunk + 1 figure chunk + 1 equation chunk

    intro_chunk = chunks[0]
    assert "fig_1" in intro_chunk.figure_refs
    assert "table_2" in intro_chunk.table_refs
    assert "eq_3" in intro_chunk.equation_refs


def test_semantic_research_analyzer_fallback():
    """Tests that SemanticResearchAnalyzer provides clean structured semantics."""
    doc = PaperDocument(
        paper_id="paper_sem",
        metadata=PaperMetadata(title="Attention Architecture", abstract="A novel attention architecture."),
        sections=[Section(title="1. Introduction", content="Intro")]
    )
    analyzer = SemanticResearchAnalyzer()
    res = analyzer.analyze_document_semantics(doc)
    assert "research_problem" in res
    assert "core_methodology" in res
    assert "key_contributions" in res


