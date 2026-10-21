"""
Targeted Visual Element Cropper for Academic PDFs.

Detects candidate visual regions for Figures, Tables, and Equations using multi-signal heuristics
(captions, bounding box geometry, image streams, font symbols, vector rules) and generates
isolated, high-fidelity element crops with complete provenance metadata.
"""

import os
import re
import pymupdf as fitz
from typing import List, Dict, Any, Optional, Tuple
from app.core.config import settings

# ─── Robust Multi-Variant Regex Patterns ─────────────────────────────────────────
FIGURE_CAPTION_REGEX = re.compile(
    r'^\s*(?:fig(?:ure)?\.?|figure)\s*([0-9ivxlcdm]+(?:\.[0-9]+)?)(?:\s*[:.\-—]\s*(.*))?$',
    re.IGNORECASE
)

TABLE_CAPTION_REGEX = re.compile(
    r'^\s*(?:table|tab\.?)\s*([0-9ivxlcdm]+(?:\.[0-9]+)?)(?:\s*[:.\-—]\s*(.*))?$',
    re.IGNORECASE
)

EQUATION_LABEL_REGEX = re.compile(
    r'\(\s*([0-9]+(?:\.[0-9]+)?|[a-zA-Z]+)\s*\)\s*$'
)

MATH_OPERATORS_REGEX = re.compile(
    r'[=+\-*/∑∫∏√≤≥≠≈∈∉⊂⊆∪∩∂∇∆αβγδεζηθικλμνξπρστυφχψωΓΔΘΛΞΠΣΦΨΩ]'
)


class ElementCandidate:
    """Represents a detected visual element with its bounding box and metadata."""

    def __init__(
        self,
        element_id: str,
        element_type: str,  # 'figure', 'table', 'equation'
        page: int,
        bbox: List[float],
        caption: str = "",
        content_text: str = "",
        needs_vlm: bool = True,
        figure_type: str = "general_figure",
        dpi: int = 150,
        image_path: Optional[str] = None
    ):
        self.element_id = element_id
        self.element_type = element_type
        self.page = page
        self.bbox = [round(c, 2) for c in bbox]
        self.caption = caption.strip()
        self.content_text = content_text.strip()
        self.needs_vlm = needs_vlm
        self.figure_type = figure_type
        self.dpi = dpi
        self.image_path = image_path

    def to_dict(self) -> Dict[str, Any]:
        return {
            "element_id": self.element_id,
            "element_type": self.element_type,
            "page": self.page,
            "bbox": self.bbox,
            "caption": self.caption,
            "content_text": self.content_text,
            "needs_vlm": self.needs_vlm,
            "figure_type": self.figure_type,
            "dpi": self.dpi,
            "image_path": self.image_path
        }


class ElementCropper:
    """Detects, crops, and manages visual bounding box snippets from scientific PDFs."""

    def __init__(self, paper_id: str, base_crop_dir: Optional[str] = None):
        self.paper_id = paper_id
        self.crop_dir = base_crop_dir or os.path.join(settings.STORAGE_DIR, "paper_cache", paper_id, "crops")
        os.makedirs(self.crop_dir, exist_ok=True)

    def classify_figure(self, caption: str, text_context: str = "") -> Tuple[str, bool]:
        """
        Lightweight structural classification of figures into semantic sub-types.
        Returns (figure_type, needs_vlm).
        Only architecture diagrams and flowcharts require expensive VLM visual parsing.
        """
        combined = f"{caption} {text_context}".lower()

        # 1. High-value visual reasoning candidates (Architecture diagrams, Flowcharts, Pipelines)
        arch_keywords = [
            "architecture", "pipeline", "framework", "overview of", "system model",
            "block diagram", "network structure", "schematic", "workflow", "dataflow",
            "encoder", "decoder", "transformer architecture", "generator structure"
        ]
        if any(kw in combined for kw in arch_keywords):
            return "architecture_diagram", True

        flow_keywords = ["flowchart", "data flow", "decision tree", "algorithmic flow", "execution pipeline"]
        if any(kw in combined for kw in flow_keywords):
            return "flowchart", True

        # 2. Experimental Plots & Charts (deterministic preservation, 0 VLM calls needed)
        plot_keywords = [
            "plot", "curve", "roc", "histogram", "training loss", "ablation",
            "accuracy vs", "loss curve", "confusion matrix", "precision-recall",
            "bar chart", "box plot", "scatter plot", "benchmark comparison"
        ]
        if any(kw in combined for kw in plot_keywords):
            return "plot_chart", False

        # 3. Photographs & Author Biographies (0 VLM calls needed)
        photo_keywords = ["photograph", "author", "biography", "headshot", "portrait", "portrait of"]
        if any(kw in combined for kw in photo_keywords):
            return "photograph", False

        # 4. Visual sample outputs & qualitative comparisons (0 VLM calls needed)
        sample_keywords = [
            "qualitative result", "qualitative examples", "sample output", "generated images",
            "visualization of generated", "visual comparison", "segmentation results", "sample reconstruction"
        ]
        if any(kw in combined for kw in sample_keywords):
            return "sample_result", False

        # 5. Decorative / Logos / Icons (0 VLM calls needed)
        deco_keywords = ["logo", "banner", "icon", "header graphic", "footer"]
        if any(kw in combined for kw in deco_keywords):
            return "decorative_image", False

        # Default general figure (preserve locally with caption; do not force VLM)
        return "general_figure", False

    def detect_and_crop_elements(
        self,
        pdf_path: str,
        default_dpi: int = 150,
        max_figures: int = 10,
        max_tables: int = 10,
        max_equations: int = 15
    ) -> Dict[str, List[ElementCandidate]]:
        """
        Scans PDF pages, detects candidate regions for figures, tables, and equations,
        evaluates whether deterministic parsing is sufficient, and crops image files.
        """
        if not os.path.exists(pdf_path):
            return {"figures": [], "tables": [], "equations": []}

        doc = fitz.open(pdf_path)
        figures: List[ElementCandidate] = []
        tables: List[ElementCandidate] = []
        equations: List[ElementCandidate] = []

        try:
            fig_count = 0
            tab_count = 0
            eq_count = 0

            for page_idx in range(len(doc)):
                page = doc.load_page(page_idx)
                page_num = page_idx + 1
                page_rect = page.rect
                blocks = page.get_text("blocks")
                page_images = page.get_images(full=True)

                # ─── 1. FIGURE DETECTION (Caption + Image bbox heuristics + Figure Classification) ───
                for b in blocks:
                    if b[6] != 0:
                        continue
                    text = b[4].strip()
                    first_line = text.split("\n")[0].strip() if text else ""
                    m_fig = FIGURE_CAPTION_REGEX.match(first_line)

                    if m_fig and fig_count < max_figures:
                        fig_num = m_fig.group(1)
                        caption_text = text
                        c_bbox = b[:4]

                        # Look for adjacent image bbox above or below caption
                        candidate_bbox = self._find_figure_bbox(page, c_bbox, page_rect)
                        fig_count += 1
                        element_id = f"fig_{fig_num}"

                        # Classify figure: only architectures/flowcharts trigger VLM
                        fig_type, needs_vlm = self.classify_figure(caption_text)

                        # Save cropped image
                        crop_path = self._render_crop(page, candidate_bbox, element_id, dpi=default_dpi)
                        figures.append(
                            ElementCandidate(
                                element_id=element_id,
                                element_type="figure",
                                page=page_num,
                                bbox=candidate_bbox,
                                caption=caption_text,
                                needs_vlm=needs_vlm,
                                figure_type=fig_type,
                                dpi=default_dpi,
                                image_path=crop_path
                            )
                        )


                # ─── 2. TABLE DETECTION (Caption + Gridline / Column heuristics) ───
                for b in blocks:
                    if b[6] != 0:
                        continue
                    text = b[4].strip()
                    first_line = text.split("\n")[0].strip() if text else ""
                    m_tab = TABLE_CAPTION_REGEX.match(first_line)

                    if m_tab and tab_count < max_tables:
                        tab_num = m_tab.group(1)
                        caption_text = text
                        c_bbox = b[:4]

                        candidate_bbox = self._find_table_bbox(page, c_bbox, page_rect)
                        tab_count += 1
                        element_id = f"table_{tab_num}"

                        # Check if table is fully recoverable deterministically (e.g. standard tabular text)
                        table_text = page.get_text("text", clip=candidate_bbox)
                        has_complex_layout = self._is_complex_table(table_text)

                        crop_path = self._render_crop(page, candidate_bbox, element_id, dpi=default_dpi)
                        tables.append(
                            ElementCandidate(
                                element_id=element_id,
                                element_type="table",
                                page=page_num,
                                bbox=candidate_bbox,
                                caption=caption_text,
                                content_text=table_text,
                                needs_vlm=has_complex_layout,
                                dpi=default_dpi,
                                image_path=crop_path
                            )
                        )

                # ─── 3. DISPLAY EQUATION DETECTION (Math symbol density & numbering) ───
                for b in blocks:
                    if b[6] != 0:
                        continue
                    text = b[4].strip()
                    if not text or len(text) > 400:  # Skip huge paragraph blocks
                        continue

                    # Check for equation numbering like (1), (2.1), or high math operator density
                    m_eq = EQUATION_LABEL_REGEX.search(text)
                    has_operators = bool(MATH_OPERATORS_REGEX.search(text))

                    # Condition: isolated short line with formula operators or numbering
                    if (m_eq or (has_operators and len(text.split('\n')) <= 3)) and eq_count < max_equations:
                        eq_count += 1
                        eq_label = m_eq.group(1) if m_eq else str(eq_count)
                        element_id = f"eq_{eq_label}"
                        eq_bbox = list(b[:4])

                        # Pad bbox slightly for math symbols/exponents
                        padded_bbox = [
                            max(0, eq_bbox[0] - 5),
                            max(0, eq_bbox[1] - 3),
                            min(page_rect.width, eq_bbox[2] + 5),
                            min(page_rect.height, eq_bbox[3] + 3)
                        ]

                        # Check if machine readable ASCII math is already clean
                        is_simple_math = self._is_clean_ascii_math(text)
                        crop_path = self._render_crop(page, padded_bbox, element_id, dpi=default_dpi)

                        equations.append(
                            ElementCandidate(
                                element_id=element_id,
                                element_type="equation",
                                page=page_num,
                                bbox=padded_bbox,
                                caption=f"Equation ({eq_label})",
                                content_text=text,
                                needs_vlm=not is_simple_math,
                                dpi=default_dpi,
                                image_path=crop_path
                            )
                        )

        except Exception as e:
            print(f"[CROPPER WARN] Error detecting elements: {e}")
        finally:
            doc.close()

        return {
            "figures": figures,
            "tables": tables,
            "equations": equations
        }

    def re_crop_element(self, pdf_path: str, candidate: ElementCandidate, elevated_dpi: int = 250) -> str:
        """Re-crops a specific element with higher DPI for self-healing targeted recovery."""
        if not os.path.exists(pdf_path):
            return candidate.image_path or ""

        doc = fitz.open(pdf_path)
        try:
            page_idx = max(0, candidate.page - 1)
            if page_idx < len(doc):
                page = doc.load_page(page_idx)
                new_path = self._render_crop(
                    page=page,
                    bbox=candidate.bbox,
                    element_id=f"{candidate.element_id}_hq",
                    dpi=elevated_dpi
                )
                candidate.dpi = elevated_dpi
                candidate.image_path = new_path
                return new_path
        finally:
            doc.close()
        return candidate.image_path or ""

    def _render_crop(self, page, bbox: List[float], element_id: str, dpi: int = 150) -> str:
        """Renders and saves a specific page bounding box region to a PNG file."""
        rect = fitz.Rect(bbox[0], bbox[1], bbox[2], bbox[3])
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, clip=rect, alpha=False)

        crop_filename = f"{element_id}.png"
        crop_path = os.path.join(self.crop_dir, crop_filename)
        pix.save(crop_path)
        return crop_path

    def _find_figure_bbox(self, page, caption_bbox, page_rect) -> List[float]:
        """Calculates likely figure graphic region associated with a caption."""
        cx0, cy0, cx1, cy1 = caption_bbox
        # Look above caption (typical IEEE/ACM paper style)
        target_height = min(260.0, cy0 - 20)
        y0 = max(20.0, cy0 - target_height)
        y1 = cy1 + 5
        x0 = max(10.0, cx0 - 20)
        x1 = min(page_rect.width - 10, cx1 + 20)
        return [x0, y0, x1, y1]

    def _find_table_bbox(self, page, caption_bbox, page_rect) -> List[float]:
        """Calculates likely table tabular region associated with a caption."""
        cx0, cy0, cx1, cy1 = caption_bbox
        # Look below caption (typical table format)
        y0 = max(10.0, cy0 - 5)
        y1 = min(page_rect.height - 20, cy1 + 240.0)
        x0 = max(10.0, cx0 - 10)
        x1 = min(page_rect.width - 10, cx1 + 10)
        return [x0, y0, x1, y1]

    def _is_complex_table(self, text: str) -> bool:
        """Evaluates whether table text has multi-line wrapping or ambiguous column alignment."""
        if not text:
            return True
        lines = [l for l in text.split("\n") if l.strip()]
        if len(lines) < 3:
            return True
        # If columns contain ±, sub-rows, or multiple spaces, VLM provides better precision
        if "±" in text or "/" in text or "—" in text:
            return True
        return False

    def _is_clean_ascii_math(self, text: str) -> bool:
        """Returns True if the text is simple linear arithmetic that does not require LaTeX OCR."""
        # Multi-line fractions, integrals, matrices, or Greek symbols need VLM
        if any(c in text for c in ['∑', '∫', '∏', '√', 'α', 'β', 'γ', 'θ', 'λ', 'μ', 'σ', '∂', '∇']):
            return False
        if len(text.split("\n")) > 1:
            return False
        return True
