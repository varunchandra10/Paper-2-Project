from pydantic import BaseModel, Field
from typing import List, Optional, Any


class PaperChunk(BaseModel):
    chunk_id: str
    paper_id: str
    section: str
    content: str
    page: Optional[int] = 1
    char_count: int = 0


def chunk_paper_document(paper_doc: Any, chunk_size: int = 500, overlap: int = 50) -> List[PaperChunk]:
    """Slices a PaperDocument into semantic layout chunks for vector RAG retrieval."""
    chunks = []
    chunk_counter = 1
    paper_id = getattr(paper_doc, "paper_id", "paper_document")
    sections = getattr(paper_doc, "sections", [])
    
    for sec in sections:
        title = getattr(sec, "title", "Main")
        content = getattr(sec, "content", "").strip()
        page_num = getattr(sec, "page_start", getattr(sec, "page", 1))
        
        if not content:
            continue
            
        words = content.split()
        if len(words) <= chunk_size:
            chunks.append(
                PaperChunk(
                    chunk_id=f"{paper_id}_c{chunk_counter}",
                    paper_id=paper_id,
                    section=title,
                    content=content,
                    page=page_num,
                    char_count=len(content)
                )
            )
            chunk_counter += 1
        else:
            start = 0
            while start < len(words):
                end = min(start + chunk_size, len(words))
                sub_text = " ".join(words[start:end])
                chunks.append(
                    PaperChunk(
                        chunk_id=f"{paper_id}_c{chunk_counter}",
                        paper_id=paper_id,
                        section=title,
                        content=sub_text,
                        page=page_num,
                        char_count=len(sub_text)
                    )
                )
                chunk_counter += 1
                start += (chunk_size - overlap)
                
    return chunks
