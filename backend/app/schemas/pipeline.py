from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum


class ProvenanceStatus(str, Enum):
    EXPLICIT = "EXPLICIT"  # Stated verbatim in paper text, backed by exact quote
    DERIVED = "DERIVED"    # Computed or calculated from explicit paper values
    INFERRED = "INFERRED"  # Deduced from architectural conventions or citations
    ASSUMED = "ASSUMED"    # Standard ML default assumed because paper is silent
    UNKNOWN = "UNKNOWN"    # Absent / not specified in paper


class ParameterDetails(BaseModel):
    value: Optional[Any] = Field(default=None, description="Extracted parameter value, or None if UNKNOWN")
    status: str = Field(default=ProvenanceStatus.UNKNOWN.value, description="Provenance status: EXPLICIT, DERIVED, INFERRED, ASSUMED, UNKNOWN")
    evidence: Optional[str] = Field(default=None, description="Exact verbatim quote from paper text supporting this value")
    source_section: Optional[str] = Field(default=None, description="Section where parameter was found")
    page: Optional[int] = Field(default=None, description="Page number where parameter was found")
    evidence_strength: str = Field(default="NONE", description="Evidence strength: STRONG, MODERATE, WEAK, NONE")
    confidence: float = Field(default=0.0, description="Calibrated confidence or strength score (0.0 to 100.0 or 0.0 to 1.0)")
    extraction_method: str = Field(default="llm_rag_extraction", description="Extraction method used")
    rationale: str = Field(default="Not specified in paper context", description="Explanation of derivation or status rationale")

    @property
    def is_known(self) -> bool:
        return self.status != ProvenanceStatus.UNKNOWN.value and self.value not in [None, "", "Not specified", "UNKNOWN"]


class Component(BaseModel):
    name: str = Field(description="The name of the component")
    type: str = Field(description="The category of the component: 'encoder', 'fusion', 'decoder', 'loss', 'training'")
    description: str = Field(default="", description="A brief description of what this component does")
    inputs: List[str] = Field(default_factory=list, description="List of input tensors")
    outputs: List[str] = Field(default_factory=list, description="List of output tensors")
    parameters: Dict[str, ParameterDetails] = Field(default_factory=dict, description="Hyperparameters for this component")


class ComponentGraph(BaseModel):
    components: List[Component] = Field(default_factory=list, description="List of all structural architecture components")
    edges: List[Dict[str, str]] = Field(default_factory=list, description="Directed data flow edges connecting components")


class ExtractedParameters(BaseModel):
    learning_rate: ParameterDetails = Field(default_factory=lambda: ParameterDetails(status="UNKNOWN", rationale="Not found in paper context"))
    batch_size: ParameterDetails = Field(default_factory=lambda: ParameterDetails(status="UNKNOWN", rationale="Not found in paper context"))
    epochs: ParameterDetails = Field(default_factory=lambda: ParameterDetails(status="UNKNOWN", rationale="Not found in paper context"))
    optimizer: ParameterDetails = Field(default_factory=lambda: ParameterDetails(status="UNKNOWN", rationale="Not found in paper context"))
    loss_function: ParameterDetails = Field(default_factory=lambda: ParameterDetails(status="UNKNOWN", rationale="Not found in paper context"))
    backbone: ParameterDetails = Field(default_factory=lambda: ParameterDetails(status="UNKNOWN", rationale="Not found in paper context"))
    custom_parameters: Dict[str, ParameterDetails] = Field(default_factory=dict)

    def get_effective_value(self, field_name: str, fallback_default: str = "") -> Tuple[str, str]:
        """
        Returns (value, status) for a parameter.
        If status is UNKNOWN or value is None, returns (fallback_default, 'ASSUMED_DEFAULT').
        """
        param = getattr(self, field_name, None)
        if param is None and field_name in self.custom_parameters:
            param = self.custom_parameters[field_name]

        if param and getattr(param, "is_known", False):
            return str(param.value), str(param.status)
        return fallback_default, "ASSUMED_DEFAULT"


class FeasibilityReport(BaseModel):
    overall_status: str = "FEASIBLE"  # FEASIBLE, FEASIBLE_WITH_MODIFICATION, NOT_FEASIBLE
    estimated_vram_gb: float = 4.2
    available_vram_gb: float = 6.0
    bottlenecks: List[str] = Field(default_factory=list)
    suggested_adaptations: List[str] = Field(default_factory=list)


class BuildSequenceStep(BaseModel):
    step_num: int
    component_name: str
    description: str
    dependencies: List[str] = Field(default_factory=list)
    file_path: str = ""


class BuildSequence(BaseModel):
    steps: List[BuildSequenceStep] = Field(default_factory=list)
    total_steps: int = 0


class ParameterApprovalRequest(BaseModel):
    custom_parameters: Dict[str, Any] = Field(default_factory=dict)
