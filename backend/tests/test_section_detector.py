import pytest
from app.extraction.constants import (
    MAJOR_HEADER_REGEX,
    ROMAN_NUMERAL_HEADER_REGEX,
    NUMBERED_HEADER_REGEX
)
from app.extraction.section_detector import detect_sections, _detect_title


def test_constants_regex_matching():
    """Verify centralized regexes match standard, Roman numeral, and hyphenated headers."""
    # Standard major headers
    assert MAJOR_HEADER_REGEX.match("Introduction") is not None
    assert MAJOR_HEADER_REGEX.match("1. Introduction") is not None
    assert MAJOR_HEADER_REGEX.match("Related-Work") is not None

    # Roman numeral headers
    m_roman1 = ROMAN_NUMERAL_HEADER_REGEX.match("III. PROPOSED ARCHITECTURE")
    assert m_roman1 is not None
    assert m_roman1.group(1) == "III"
    assert m_roman1.group(2) == "PROPOSED ARCHITECTURE"

    m_roman2 = ROMAN_NUMERAL_HEADER_REGEX.match("IV. EXPERIMENTS")
    assert m_roman2 is not None
    assert m_roman2.group(1) == "IV"
    assert m_roman2.group(2) == "EXPERIMENTS"

    # Numbered headers with hyphens
    m_hyphen = NUMBERED_HEADER_REGEX.match("2. SYSTEM-DESIGN")
    assert m_hyphen is not None
    assert m_hyphen.group(1) == "2"
    assert m_hyphen.group(2) == "SYSTEM-DESIGN"


def test_detect_title_font_heuristic():
    """Verify _detect_title finds title with largest font size on page 1."""
    pages_data = [
        {
            "page": 1,
            "blocks": [
                {"text": "arXiv:2301.00001v1 [cs.CV] 1 Jan 2023", "font_size": 9.0},
                {"text": "Dual Code Engine for Neural Synthesis", "font_size": 18.0},
                {"text": "John Doe, Jane Smith", "font_size": 11.0},
                {"text": "Abstract — We present a novel framework...", "font_size": 10.0}
            ]
        }
    ]
    title = _detect_title(pages_data)
    assert title == "Dual Code Engine for Neural Synthesis"


def test_font_aware_and_roman_numeral_section_detection():
    """Verify font size heuristics (> 1.1x) and Roman numerals in detect_sections."""
    pages_data = [
        {
            "page": 1,
            "blocks": [
                {"text": "Abstract — This paper introduces deep learning pipelines.", "font_size": 10.0, "font_name": "Times"},
                {"text": "III. PROPOSED ARCHITECTURE\nOur architecture consists of three components.", "font_size": 10.0, "font_name": "Times"},
                {"text": "The encoder takes raw input tensors and applies multi-head self-attention.", "font_size": 10.0, "font_name": "Times"}
            ]
        },
        {
            "page": 2,
            "blocks": [
                # Unnumbered section header using large font (14pt vs 10pt baseline)
                {"text": "Ablation Studies", "font_size": 14.0, "font_name": "Times-Bold"},
                {"text": "We evaluate the impact of removing the auxiliary loss function.", "font_size": 10.0, "font_name": "Times"},
                # Unnumbered subsection using bold font
                {"text": "Effect of Learning Rate", "font_size": 10.0, "font_name": "Helvetica-Bold"},
                {"text": "Lower learning rates yield smoother convergence across all seeds.", "font_size": 10.0, "font_name": "Times"}
            ]
        }
    ]

    res = detect_sections(pages_data)
    sections = res["sections"]

    # 1. Abstract detected
    assert "Abstract" in sections
    assert "This paper introduces deep learning pipelines." in sections["Abstract"]["content"]

    # 2. Roman numeral header detected
    assert any("PROPOSED ARCHITECTURE" in sec for sec in sections)
    arch_key = [k for k in sections if "PROPOSED ARCHITECTURE" in k][0]
    assert "III" in arch_key
    assert sections[arch_key]["page_start"] == 1

    # 3. Unnumbered header via font size heuristic (> 1.1x)
    assert any("Ablation Studies" in sec for sec in sections)
    abl_key = [k for k in sections if "Ablation Studies" in k][0]
    assert sections[abl_key]["page_start"] == 2

    # 4. Bold unnumbered subsection
    assert "Effect of Learning Rate" in sections[abl_key]["subsections"]
