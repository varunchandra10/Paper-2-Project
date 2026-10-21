"""
Provenance-Aware Hierarchical Document Chunker.

Slices canonical PaperDocuments into structured RAG vector chunks with embedded
element references (Figures, Tables, Equations), page provenance, and source metadata.
"""

import re
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict


class PaperChunk(BaseModel):
    chunk_id: str
    paper_id: str
    section: str
    content: str
    page: Optional[int] = 1
    char_count: int = 0
    source_type: str = "paragraph"  # 'paragraph', 'table', 'figure', 'equation'
    figure_refs: List[str] = Field(default_factory=list)
    table_refs: List[str] = Field(default_factory=list)
    equation_refs: List[str] = Field(default_factory=list)
    source: Optional[Dict[str, Any]] = None


def _find_references(text: str) -> tuple:
    """Detects in-text references to figures, tables, and equations."""
    fig_refs = [f"fig_{m.group(1)}" for m in re.finditer(r'\b(?:fig(?:ure)?\.?)\s*([0-9]+)', text, re.IGNORECASE)]
    tab_refs = [f"table_{m.group(1)}" for m in re.finditer(r'\b(?:table|tab\.?)\s*([0-9]+)', text, re.IGNORECASE)]
    eq_refs = [f"eq_{m.group(1)}" for m in re.finditer(r'\b(?:eq(?:uation)?\.?)\s*(?:\(?\s*([0-9]+)\s*\)?)', text, re.IGNORECASE)]
    return list(set(fig_refs)), list(set(tab_refs)), list(set(eq_refs))


def chunk_paper_document(paper_doc: Any, chunk_size: int = 500, overlap: int = 50) -> List[PaperChunk]:
    """
    Slices a PaperDocument into hierarchical semantic chunks preserving cross-references.
    """
    chunks = []
    chunk_counter = 1
    paper_id = getattr(paper_doc, "paper_id", "paper_document")
    sections = getattr(paper_doc, "sections", [])

    # ── 1. Chunk Section Paragraphs ──
    for sec in sections:
        title = getattr(sec, "title", "Main")
        content = getattr(sec, "content", "").strip()
        page_num = getattr(sec, "page_start", getattr(sec, "page", 1))

        if not content:
            continue

        words = content.split()
        if len(words) <= chunk_size:
            f_refs, t_refs, e_refs = _find_references(content)
            chunks.append(
                PaperChunk(
                    chunk_id=f"{paper_id}_c{chunk_counter}",
                    paper_id=paper_id,
                    section=title,
                    content=content,
                    page=page_num,
                    char_count=len(content),
                    source_type="paragraph",
                    figure_refs=f_refs,
                    table_refs=t_refs,
                    equation_refs=e_refs,
                    source={"page": page_num, "section": title}
                )
            )
            chunk_counter += 1
        else:
            start = 0
            while start < len(words):
                end = min(start + chunk_size, len(words))
                sub_text = " ".join(words[start:end])
                f_refs, t_refs, e_refs = _find_references(sub_text)
                chunks.append(
                    PaperChunk(
                        chunk_id=f"{paper_id}_c{chunk_counter}",
                        paper_id=paper_id,
                        section=title,
                        content=sub_text,
                        page=page_num,
                        char_count=len(sub_text),
                        source_type="paragraph",
                        figure_refs=f_refs,
                        table_refs=t_refs,
                        equation_refs=e_refs,
                        source={"page": page_num, "section": title}
                    )
                )
                chunk_counter += 1
                start += (chunk_size - overlap)

    # ── 2. Create Specialized Chunks for Tables ──
    for tab in getattr(paper_doc, "tables", []):
        md = getattr(tab, "content_markdown", "")
        cap = getattr(tab, "caption", "")
        if md:
            tab_text = f"### {cap}\n{md}"
            chunks.append(
                PaperChunk(
                    chunk_id=f"{paper_id}_c{chunk_counter}",
                    paper_id=paper_id,
                    section="Tables",
                    content=tab_text,
                    page=getattr(tab, "page", 1),
                    char_count=len(tab_text),
                    source_type="table",
                    table_refs=[getattr(tab, "id", "")],
                    source={"element_id": getattr(tab, "id", ""), "page": getattr(tab, "page", 1)}
                )
            )
            chunk_counter += 1

    # ── 3. Create Specialized Chunks for Figures with Visual Descriptions ──
    for fig in getattr(paper_doc, "figures", []):
        desc = getattr(fig, "visual_description", None)
        cap = getattr(fig, "caption", "")
        if desc:
            fig_text = f"### {cap}\nVisual Description: {desc}"
        elif cap:
            fig_text = f"### {cap}"
        else:
            continue

        chunks.append(
            PaperChunk(
                chunk_id=f"{paper_id}_c{chunk_counter}",
                paper_id=paper_id,
                section="Figures",
                content=fig_text,
                page=getattr(fig, "page", 1),
                char_count=len(fig_text),
                source_type="figure",
                figure_refs=[getattr(fig, "id", "")],
                source={"element_id": getattr(fig, "id", ""), "page": getattr(fig, "page", 1)}
            )
        )
        chunk_counter += 1


    # ── 4. Create Specialized Chunks for Equations ──
    for eq in getattr(paper_doc, "equations", []):
        latex = getattr(eq, "latex", "")
        cap = getattr(eq, "caption", "") or "Equation"
        if latex:
            eq_text = f"### {cap}\nLaTeX Formulation:\n$$\n{latex}\n$$"
            chunks.append(
                PaperChunk(
                    chunk_id=f"{paper_id}_c{chunk_counter}",
                    paper_id=paper_id,
                    section="Equations",
                    content=eq_text,
                    page=getattr(eq, "page", 1),
                    char_count=len(eq_text),
                    source_type="equation",
                    equation_refs=[getattr(eq, "id", "")],
                    source={"element_id": getattr(eq, "id", ""), "page": getattr(eq, "page", 1)}
                )
            )
            chunk_counter += 1

    return chunks
