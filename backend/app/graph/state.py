from typing import TypedDict, List, Dict, Any, Optional
from app.schemas.paper import PaperMetadata, PaperDocument
from app.schemas.pipeline import ExtractedParameters, FeasibilityReport, BuildSequence


class PipelineState(TypedDict):
    pdf_path: str
    constraints: dict
    model_name: str
    loop_count: int
    raw_sections: dict
    metadata: PaperMetadata
    paper_doc: PaperDocument
    component_graph: dict
    extracted_parameters: ExtractedParameters
    feasibility_report: FeasibilityReport
    build_sequence: BuildSequence
    generate_code_requested: bool
    parameters_approved: bool
    report: dict
