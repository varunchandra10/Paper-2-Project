from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from app.schemas.pipeline_schemas import PaperMetadata


class Provenance(BaseModel):
    """Origin coordinate details tracking where a claim or text was extracted."""
    page: int = Field(default=1, description="1-based page number within the PDF")
    section: str = Field(default="Main", description="The section name or header matching the block's parent")
    text_span: str = Field(default="", description="Exact snippet text block matching the value")


class SourceValue(BaseModel):
    """Wrapper carrying a parameter value along with its provenance and extraction status."""
    value: Any = Field(description="The parameter value or object content")
    source: Provenance = Field(default_factory=Provenance, description="Provenance source coordinates")
    status: str = Field(
        default="EXPLICIT",
        description="Confidence status. Must be one of: 'EXPLICIT', 'DERIVED', 'EXTERNAL', 'ASSUMED', 'UNKNOWN'"
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Extraction confidence score from 0.0 to 1.0"
    )


class Section(BaseModel):
    """Represents a hierarchical document section containing text content and subheadings."""
    title: str = Field(description="The section header name")
    content: str = Field(description="Full text paragraphs merged inside this section")
    subsections: Dict[str, str] = Field(
        default_factory=dict,
        description="Dictionary mapping subsection subheadings to their respective text content"
    )
    page_start: int = Field(default=1, description="The 1-based page number where this section starts")
    page_end: int = Field(default=1, description="The 1-based page number where this section ends")


class Figure(BaseModel):
    """Represents an extracted figure or image object from the paper layout."""
    id: str = Field(description="Unique figure identifier (e.g. 'fig_1')")
    caption: str = Field(default="", description="Full caption text associated with this figure")
    page: int = Field(default=1, description="1-based page number containing the figure")


class Table(BaseModel):
    """Represents a structured scientific table extracted in Markdown format."""
    id: str = Field(description="Unique table identifier (e.g. 'tab_1')")
    caption: str = Field(default="", description="Full caption text associated with this table")
    content_markdown: str = Field(default="", description="Markdown-formatted tabular string representation")
    page: int = Field(default=1, description="1-based page number containing the table")


class Equation(BaseModel):
    """Represents a mathematical equation parsed from the document."""
    id: str = Field(description="Unique equation identifier (e.g. 'eq_1')")
    latex: str = Field(description="LaTeX string representation of the equation")
    page: int = Field(default=1, description="1-based page number containing the equation")
    caption: Optional[str] = Field(default=None, description="Optional caption or identifier name")


class Algorithm(BaseModel):
    """Represents pseudocode or algorithm listings from the paper."""
    id: str = Field(description="Unique algorithm identifier (e.g. 'alg_1')")
    caption: str = Field(default="", description="Caption text for this algorithm")
    pseudocode: str = Field(default="", description="The raw pseudocode lines or logic text block")
    page: int = Field(default=1, description="1-based page number containing the algorithm")


class Citation(BaseModel):
    """Represents an in-text citation marker (e.g. '[12]')."""
    citation_id: str = Field(description="The citation ID string matching the references list (e.g. '[12]')")
    target_text: str = Field(default="", description="Context text immediately surrounding the citation marker")
    source: Provenance = Field(default_factory=Provenance, description="Provenance coordinate location of the citation marker")


class Reference(BaseModel):
    """Represents a single bibliography citation entry from the end of the paper."""
    ref_id: str = Field(description="The bibliography key (e.g. '[12]' or '12')")
    citation_text: str = Field(description="The complete parsed citation string (title, authors, journal, year)")


class PageInfo(BaseModel):
    """Represents page-level metrics extracted during inspection."""
    page: int = Field(description="1-based page number")
    width: float = Field(default=595.0, description="Page width dimension in points")
    height: float = Field(default=842.0, description="Page height dimension in points")
    character_count: int = Field(default=0, description="Total characters extracted from this page")


class PaperDocument(BaseModel):
    """The root canonical paper schema representing an entire extracted scientific document."""
    paper_id: str = Field(description="Unique normalized paper ID (prefixed with paper_)")
    metadata: PaperMetadata = Field(default_factory=PaperMetadata, description="Clean paper metadata")
    sections: List[Section] = Field(default_factory=list, description="Hierarchical section tree list")
    figures: List[Figure] = Field(default_factory=list, description="Visual figures list")
    tables: List[Table] = Field(default_factory=list, description="Scientific tables list")
    equations: List[Equation] = Field(default_factory=list, description="Mathematical equations list")
    algorithms: List[Algorithm] = Field(default_factory=list, description="Pseudocode algorithms list")
    citations: List[Citation] = Field(default_factory=list, description="In-text citations coordinates")
    references: List[Reference] = Field(default_factory=list, description="Bibliography citations list")
    pages: List[PageInfo] = Field(default_factory=list, description="Individual page-level metrics")
    extraction_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Tracks layout type, date of extraction, and list of selected routed parsers"
    )


class ValidationMetric(BaseModel):
    """Holds status, summary message, and detailed notes for a specific validation check."""
    status: str = Field(description="Must be one of: 'SUCCESS', 'WARNING', 'ERROR'")
    message: str = Field(description="Summary message of the validation result")
    details: Optional[str] = Field(default=None, description="Detailed anomalies or debug lists")


class ExtractionQualityReport(BaseModel):
    """Summarizes validation quality metrics and records any conflicting extractions."""
    paper_id: str = Field(description="Normalized paper ID")
    valid: bool = Field(default=True, description="True if the document contains zero 'ERROR' flags")
    completeness_score: Optional[float] = Field(default=None, description="Quality completeness score percentage from 0 to 100")
    scorecard: Dict[str, ValidationMetric] = Field(
        default_factory=dict,
        description="Key-value scorecard mapping validation checks to their status metrics"
    )
    conflicts_logged: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of conflicts or parsing discrepancies logged during extraction"
    )
