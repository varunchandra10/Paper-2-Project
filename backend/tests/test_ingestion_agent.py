import pytest
from app.agents.ingestion_agent import (
    _is_valid_title,
    _clean_title,
    _TITLE_REJECT,
    _TITLE_MIN,
    _TITLE_MAX
)


# ── _is_valid_title & _TITLE_REJECT tests ─────────────────────────────────────

def test_is_valid_title_legitimate_titles():
    """Verifies that standard research paper titles pass the validity checks."""
    valid_titles = [
        "Attention Is All You Need: Deep Learning for Sequence Modeling",
        "Deep Residual Learning for Image Recognition and Feature Extraction",
        "Generative Adversarial Nets with Conditional Latent Spaces",
        "RoBERTa: A Robustly Optimized BERT Pretraining Approach"
    ]
    for title in valid_titles:
        assert _is_valid_title(title) is True, f"Failed for valid title: {title}"


def test_is_valid_title_too_short():
    """Verifies that titles under _TITLE_MIN (15 characters) are rejected."""
    short_titles = ["", "AI", "Transformers", "Short title", "   12345678   "]
    for title in short_titles:
        assert _is_valid_title(title) is False, f"Expected False for short title: '{title}'"


def test_is_valid_title_too_long():
    """Verifies that titles exceeding _TITLE_MAX (300 characters) are rejected."""
    oversized = "A" * 305
    assert _is_valid_title(oversized) is False


def test_is_valid_title_reject_doi():
    """Verifies rejection of DOI identifiers mistaken for paper titles."""
    assert _is_valid_title("doi: 10.1145/3318464.3389700 Research Paper") is False
    assert _is_valid_title("DOI : 10.1016/j.neucom.2021.05.001 Title Here") is False


def test_is_valid_title_reject_arxiv():
    """Verifies rejection of arXiv stamps and identifiers."""
    assert _is_valid_title("arXiv: 2301.12345v1 [cs.CV] Deep Neural Architectures") is False
    assert _is_valid_title("arxiv:2106.09685 Parameter-Efficient Transfer Learning") is False


def test_is_valid_title_reject_publishers():
    """Verifies rejection of publisher header banners (IEEE, Elsevier, Springer, MDPI)."""
    assert _is_valid_title("IEEE Transactions on Neural Networks and Learning Systems") is False
    assert _is_valid_title("Elsevier Inc. All rights reserved. Machine Learning Journal") is False
    assert _is_valid_title("Springer Nature Switzerland AG 2023 Computer Vision Lecture Notes") is False
    assert _is_valid_title("MDPI Open Access Publishing Remote Sensing Technologies") is False


def test_is_valid_title_reject_journal_metadata():
    """Verifies rejection of journal volume, issue, received/accepted dates, and pages."""
    assert _is_valid_title("Volume 34, Issue 2, March 2024, Pages 100-115") is False
    assert _is_valid_title("Journal of Machine Learning Research 22 (2021) 1-48") is False
    assert _is_valid_title("Proceedings of the 38th International Conference on Machine Learning") is False
    assert _is_valid_title("Manuscript ID: 987654 under review for IEEE PAMI") is False
    assert _is_valid_title("Preprint submitted to Elsevier for peer review") is False


def test_is_valid_title_reject_low_alpha_ratio():
    """Verifies rejection of formulas, numeric tables, or symbols with alpha ratio < 0.40."""
    mostly_symbols = "12345-67890 (+++ --- *** /// === %%% @@@ $$$) #!?"
    assert _is_valid_title(mostly_symbols) is False


# ── _clean_title tests ────────────────────────────────────────────────────────

def test_clean_title_normalizes_whitespace():
    """Verifies that excessive whitespace, tabs, and newlines are collapsed to single spaces."""
    raw = "  Convolutional \t Neural \n\n Networks   for Vision   "
    assert _clean_title(raw) == "Convolutional Neural Networks for Vision"


def test_clean_title_removes_leading_numbers():
    """Verifies stripping of leading chapter or section numbering."""
    assert _clean_title("1. Introduction to Foundation Models") == "Introduction to Foundation Models"
    assert _clean_title("12  Robust Policy Optimization") == "Robust Policy Optimization"
    assert _clean_title("03.4 Scaled Attention Mechanisms") == "4 Scaled Attention Mechanisms"
