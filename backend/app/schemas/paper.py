from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class PaperMetadata(BaseModel):
    title: str = "Untitled Paper"
    authors: List[str] = Field(default_factory=list)
    year: Optional[int] = None
    venue: Optional[str] = None
    doi: Optional[str] = None
    abstract: str = ""
    domain: str = "Deep Learning / Remote Sensing"
    scholar_tldr: Optional[str] = None
    citations: Optional[int] = None


class PaperSection(BaseModel):
    title: str
    content: str
    section_num: Optional[str] = None
    page: Optional[int] = None


class PaperDocument(BaseModel):
    paper_id: str
    metadata: PaperMetadata
    sections: List[PaperSection] = Field(default_factory=list)
    tables: List[Dict[str, Any]] = Field(default_factory=list)
    figures: List[Dict[str, Any]] = Field(default_factory=list)
    raw_full_text: str = ""
