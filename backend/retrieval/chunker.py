import re
from typing import List, Dict, Any
from schemas.canonical_paper import PaperDocument
from schemas.rag_schemas import PaperChunk


def chunk_paper_document(
    doc: PaperDocument,
    max_chunk_chars: int = 1200,
    min_chunk_chars: int = 150
) -> List[PaperChunk]:
    """
    Slices a canonical PaperDocument into semantically isolated, layout-aware PaperChunks.
    Preserves tables, equations, figures, and algorithms as distinct, self-contained units.
    """
    chunks = []
    chunk_index = 1
    paper_id = doc.paper_id

    # Helper function to generate standardized chunk objects
    def add_chunk(content: str, section: str, subsection: str, page: int, content_type: str, source_id: str, extra_meta: dict = None):
        nonlocal chunk_index
        cid = f"{paper_id}_chunk_{chunk_index:03d}"
        meta = extra_meta or {}
        chunks.append(
            PaperChunk(
                chunk_id=cid,
                paper_id=paper_id,
                content=content.strip(),
                section=section,
                subsection=subsection or "None",
                page=page,
                content_type=content_type,
                source_id=source_id,
                metadata=meta
            )
        )
        chunk_index += 1

    # --- 1. Process Section & Subsection Text Chunks ---
    for sec in doc.sections:
        # Process main section body text
        if sec.content.strip():
            paragraphs = [p.strip() for p in re.split(r'\n\s*\n', sec.content) if p.strip()]
            
            current_buffer = []
            current_len = 0
            
            for p in paragraphs:
                p_len = len(p)
                
                # If paragraph itself exceeds max limit, we split it by sentences
                if p_len > max_chunk_chars:
                    # Flush current buffer first
                    if current_buffer:
                        add_chunk(
                            content=" ".join(current_buffer),
                            section=sec.title,
                            subsection="None",
                            page=sec.page_start,
                            content_type="text",
                            source_id=_slugify(sec.title)
                        )
                        current_buffer = []
                        current_len = 0
                        
                    # Split massive paragraph into sentence chunks
                    sentences = [s.strip() for s in re.split(r'\.\s+', p) if s.strip()]
                    sent_buffer = []
                    sent_len = 0
                    for s in sentences:
                        s_text = s + "."
                        s_len = len(s_text)
                        if sent_len + s_len > max_chunk_chars:
                            if sent_buffer:
                                add_chunk(
                                    content=" ".join(sent_buffer),
                                    section=sec.title,
                                    subsection="None",
                                    page=sec.page_start,
                                    content_type="text",
                                    source_id=_slugify(sec.title)
                                )
                            sent_buffer = [s_text]
                            sent_len = s_len
                        else:
                            sent_buffer.append(s_text)
                            sent_len += s_len
                    if sent_buffer:
                        add_chunk(
                            content=" ".join(sent_buffer),
                            section=sec.title,
                            subsection="None",
                            page=sec.page_start,
                            content_type="text",
                            source_id=_slugify(sec.title)
                        )
                # If paragraph fits, group with previous if it's too small
                elif current_len + p_len > max_chunk_chars:
                    add_chunk(
                        content=" ".join(current_buffer),
                        section=sec.title,
                        subsection="None",
                        page=sec.page_start,
                        content_type="text",
                        source_id=_slugify(sec.title)
                    )
                    current_buffer = [p]
                    current_len = p_len
                else:
                    current_buffer.append(p)
                    current_len += p_len
            
            if current_buffer:
                add_chunk(
                    content=" ".join(current_buffer),
                    section=sec.title,
                    subsection="None",
                    page=sec.page_start,
                    content_type="text",
                    source_id=_slugify(sec.title)
                )

        # Process subsections individually to preserve context boundaries
        for sub_title, sub_content in sec.subsections.items():
            if not sub_content.strip():
                continue
                
            sub_paragraphs = [p.strip() for p in re.split(r'\n\s*\n', sub_content) if p.strip()]
            current_buffer = []
            current_len = 0
            
            for p in sub_paragraphs:
                p_len = len(p)
                if p_len > max_chunk_chars:
                    if current_buffer:
                        add_chunk(
                            content=" ".join(current_buffer),
                            section=sec.title,
                            subsection=sub_title,
                            page=sec.page_start,
                            content_type="text",
                            source_id=_slugify(sub_title)
                        )
                        current_buffer = []
                        current_len = 0
                    
                    sentences = [s.strip() for s in re.split(r'\.\s+', p) if s.strip()]
                    sent_buffer = []
                    sent_len = 0
                    for s in sentences:
                        s_text = s + "."
                        s_len = len(s_text)
                        if sent_len + s_len > max_chunk_chars:
                            if sent_buffer:
                                add_chunk(
                                    content=" ".join(sent_buffer),
                                    section=sec.title,
                                    subsection=sub_title,
                                    page=sec.page_start,
                                    content_type="text",
                                    source_id=_slugify(sub_title)
                                )
                            sent_buffer = [s_text]
                            sent_len = s_len
                        else:
                            sent_buffer.append(s_text)
                            sent_len += s_len
                    if sent_buffer:
                        add_chunk(
                            content=" ".join(sent_buffer),
                            section=sec.title,
                            subsection=sub_title,
                            page=sec.page_start,
                            content_type="text",
                            source_id=_slugify(sub_title)
                        )
                elif current_len + p_len > max_chunk_chars:
                    add_chunk(
                        content=" ".join(current_buffer),
                        section=sec.title,
                        subsection=sub_title,
                        page=sec.page_start,
                        content_type="text",
                        source_id=_slugify(sub_title)
                    )
                    current_buffer = [p]
                    current_len = p_len
                else:
                    current_buffer.append(p)
                    current_len += p_len
                    
            if current_buffer:
                add_chunk(
                    content=" ".join(current_buffer),
                    section=sec.title,
                    subsection=sub_title,
                    page=sec.page_start,
                    content_type="text",
                    source_id=_slugify(sub_title)
                )

    # --- 2. Process Tables as First-Class Chunks ---
    for tbl in doc.tables:
        table_content = f"Table ID: {tbl.id}\nCaption: {tbl.caption}\n\n{tbl.content_markdown}"
        add_chunk(
            content=table_content,
            section="Scientific Tables",
            subsection="None",
            page=tbl.page,
            content_type="table",
            source_id=tbl.id,
            extra_meta={"caption": tbl.caption}
        )

    # --- 3. Process Figures as First-Class Chunks ---
    for fig in doc.figures:
        fig_content = f"Figure ID: {fig.id}\nCaption: {fig.caption}"
        add_chunk(
            content=fig_content,
            section="Figures List",
            subsection="None",
            page=fig.page,
            content_type="figure",
            source_id=fig.id,
            extra_meta={"caption": fig.caption}
        )

    # --- 4. Process Equations as First-Class Chunks ---
    for eq in doc.equations:
        caption_str = f"Caption: {eq.caption}\n" if eq.caption else ""
        eq_content = f"Equation ID: {eq.id}\n{caption_str}LaTeX Formula: {eq.latex}"
        add_chunk(
            content=eq_content,
            section="Mathematical Equations",
            subsection="None",
            page=eq.page,
            content_type="equation",
            source_id=eq.id,
            extra_meta={"latex": eq.latex}
        )

    # --- 5. Process Algorithms as First-Class Chunks ---
    for alg in doc.algorithms:
        alg_content = f"Algorithm ID: {alg.id}\nCaption: {alg.caption}\n\nPseudocode:\n{alg.pseudocode}"
        add_chunk(
            content=alg_content,
            section="Algorithms List",
            subsection="None",
            page=alg.page,
            content_type="algorithm",
            source_id=alg.id,
            extra_meta={"caption": alg.caption}
        )

    return chunks


def _slugify(text: str) -> str:
    """Helper to convert section titles into clean source identifiers."""
    slug = text.lower().strip()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s-]+', '_', slug)
    return slug
