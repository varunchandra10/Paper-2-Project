from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class PaperChunk(BaseModel):
    """Represents a semantically isolated retrieval unit from a research paper."""
    chunk_id: str = Field(description="Unique chunk identifier (e.g. paper_1_chunk_12)")
    paper_id: str = Field(description="Normalized paper ID")
    content: str = Field(description="The clean text, markdown table, or pseudocode content")
    section: str = Field(default="main", description="Primary section heading name")
    subsection: Optional[str] = Field(default=None, description="Subheading name if applicable")
    page: int = Field(default=1, description="1-based page number where this content originates")
    content_type: str = Field(default="text", description="Must be one of: 'text', 'table', 'figure', 'equation', 'algorithm'")
    source_id: str = Field(default="", description="Identifier mapping to the source object")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context coordinates")
