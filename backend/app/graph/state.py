from typing import TypedDict, List, Dict, Any, Optional
from app.schemas.paper import PaperMetadata, PaperDocument
from app.schemas.pipeline import ExtractedParameters, FeasibilityReport, BuildSequence


class PipelineState(TypedDict, total=False):
    """Explicit LangGraph V2 Pipeline State with execution bounds, provenance, and retry tracking."""
    job_id: str
    pdf_path: str
    paper_id: str
    constraints: dict
    model_name: str
    loop_count: int
    raw_sections: dict
    metadata: PaperMetadata
    paper_doc: PaperDocument
    component_graph: dict
    extracted_parameters: ExtractedParameters
    feasibility_report: FeasibilityReport
    feasibility_loop_count: int
    max_feasibility_retries: int
    build_sequence: BuildSequence
    specification: dict
    generate_code_requested: bool
    sample_code: str
    generated_code: Dict[str, str]
    verification_result: dict
    code_repair_loop_count: int
    max_repair_retries: int
    parameters_approved: bool
    report: dict
    history_trace: List[dict]
    execution_bounds: dict
    status: str
