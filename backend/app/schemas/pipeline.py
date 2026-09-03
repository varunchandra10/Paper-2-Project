from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class ParameterDetails(BaseModel):
    value: Any
    confidence: int = 100
    status: str = "EXTRACTED"  # EXPLICIT, IMPLICIT, ASSUMED, USER_DEFINED
    rationale: str = ""
    source_section: str = ""


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
    learning_rate: ParameterDetails = Field(default_factory=lambda: ParameterDetails(value="0.0001", confidence=90))
    batch_size: ParameterDetails = Field(default_factory=lambda: ParameterDetails(value="4", confidence=95))
    epochs: ParameterDetails = Field(default_factory=lambda: ParameterDetails(value="50", confidence=90))
    optimizer: ParameterDetails = Field(default_factory=lambda: ParameterDetails(value="AdamW", confidence=95))
    loss_function: ParameterDetails = Field(default_factory=lambda: ParameterDetails(value="CrossEntropyLoss", confidence=90))
    backbone: ParameterDetails = Field(default_factory=lambda: ParameterDetails(value="Swin-T", confidence=85))
    custom_parameters: Dict[str, ParameterDetails] = Field(default_factory=dict)


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
