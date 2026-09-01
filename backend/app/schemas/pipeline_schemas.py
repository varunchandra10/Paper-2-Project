from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

# Day 1 & Day 2 schemas
class SectionInfo(BaseModel):
    title: str = Field(description="The exact title of the section (e.g., 'I. INTRODUCTION', 'III. METHOD')")
    character_count: int = Field(description="Length of the section content in characters")

class PaperMetadata(BaseModel):
    title: str = Field(default="Untitled Paper", description="The official title of the research paper")
    authors: List[str] = Field(default_factory=list, description="List of author names extracted from the paper")
    abstract: str = Field(default="", description="The full abstract of the paper")
    sections_found: List[SectionInfo] = Field(default_factory=list, description="List of all sections parsed in the paper")
    primary_contribution: str = Field(default="", description="A concise summary of the paper's primary contribution")
    scholar_tldr: Optional[str] = Field(default=None, description="TL;DR summary retrieved from Semantic Scholar API")
    citation_count: Optional[int] = Field(default=None, description="Citation count from Semantic Scholar API")

# Day 3, 4, 5 schemas (Component Graph & Parameter Details)
class ParameterDetails(BaseModel):
    value: str = Field(default="Not specified", description="The extracted value of the parameter")
    confidence: str = Field(default="INFERRED", description="Confidence tagging: 'CONFIRMED' / 'INFERRED' / 'ASSUMED'")
    rationale: str = Field(default="Not specified", description="Brief explanation of the source or logic used")

class Component(BaseModel):
    name: str = Field(description="The name of the component")
    type: str = Field(description="The category of the component: 'encoder', 'fusion', 'decoder', 'loss', 'training'")
    description: str = Field(default="", description="A brief description of what this component does")
    inputs: List[str] = Field(default_factory=list, description="List of input tensors")
    outputs: List[str] = Field(default_factory=list, description="List of output tensors")
    parameters: Dict[str, ParameterDetails] = Field(
        default_factory=dict,
        description="Mapping of hyperparameter names to their details"
    )

class ComponentGraph(BaseModel):
    components: List[Component] = Field(default_factory=list, description="List of all structural architecture components")
    edges: List[Dict[str, str]] = Field(
        default_factory=list, 
        description="Directed data flow edges connecting components"
    )

class PipelineOutput(BaseModel):
    metadata: PaperMetadata = Field(default_factory=PaperMetadata, description="Structured metadata of the research paper")
    component_graph: ComponentGraph = Field(default_factory=ComponentGraph, description="Structured component graph")

class ComponentFeasibility(BaseModel):
    component_name: str = Field(description="The name of the component being analyzed")
    status: str = Field(default="FEASIBLE", description="Feasibility status: 'FEASIBLE', 'WARNING', 'IMPOSSIBLE'")
    reason: str = Field(default="Component parameters fit within hardware constraints.", description="Technical reason for status.")
    suggested_substitute: str = Field(default="None needed", description="One concrete actionable suggestion.")

class AlternativePlatform(BaseModel):
    platform_name: str = Field(description="Name of the cloud platform")
    description: str = Field(description="Brief details of what this platform offers")
    how_to_use: str = Field(description="Actionable step-by-step guidance")

class FeasibilityReport(BaseModel):
    overall_status: str = Field(default="FEASIBLE", description="Overall project feasibility status")
    components_analysis: List[ComponentFeasibility] = Field(default_factory=list, description="List of component reports")
    training_status: str = Field(default="FEASIBLE", description="Training regime feasibility status")
    training_reason: str = Field(default="Training parameters fit expected GPU VRAM.", description="Detailed reason")
    training_substitute: str = Field(default="None needed", description="Suggested swap for training parameters")
    recommendations: List[str] = Field(default_factory=list, description="Actionable summary of recommendations")
    alternatives: List[AlternativePlatform] = Field(default_factory=list, description="List of free or low-cost cloud platforms")

    @property
    def components(self) -> List[ComponentFeasibility]:
        return self.components_analysis

class Milestone(BaseModel):
    id: int = Field(description="Step sequence number")
    name: str = Field(description="Name of the build milestone")
    objectives: List[str] = Field(default_factory=list, description="Core technical tasks")
    components_involved: List[str] = Field(default_factory=list, description="Names of components involved")
    estimated_complexity: str = Field(default="MEDIUM", description="Complexity: 'LOW' / 'MEDIUM' / 'HIGH'")
    estimated_duration_days: int = Field(default=3, description="Estimated days to complete milestone")
    priority: str = Field(default="MEDIUM", description="Priority level: 'LOW' / 'MEDIUM' / 'HIGH' / 'CRITICAL'")
    dependency_rationale: str = Field(default="", description="Explanation of sequence rationale")

class BuildSequence(BaseModel):
    milestones: List[Milestone] = Field(default_factory=list, description="Ordered list of build milestones")
    total_duration_weeks: float = Field(default=0.0, description="Total estimated project duration in weeks")

class ProjectParameter(BaseModel):
    value: str = Field(default="Not specified", description="The extracted parameter value")
    source: str = Field(default="Section III", description="Exact source location in the paper")
    status: str = Field(default="EXPLICIT", description="Provenance status: 'EXPLICIT', 'INFERRED', 'ASSUMED'")
    confidence: float = Field(default=1.0, description="Confidence rating from 0.0 to 1.0")

class ExtractedParameters(BaseModel):
    model: ProjectParameter = Field(default_factory=ProjectParameter, description="Model architecture/backbone name")
    dataset: ProjectParameter = Field(default_factory=ProjectParameter, description="Dataset used for evaluation/training")
    optimizer: ProjectParameter = Field(default_factory=ProjectParameter, description="Optimization algorithm used")
    learning_rate: ProjectParameter = Field(default_factory=ProjectParameter, description="Base learning rate parameter")
    batch_size: ProjectParameter = Field(default_factory=ProjectParameter, description="Training batch size")
    epochs: ProjectParameter = Field(default_factory=ProjectParameter, description="Number of training epochs")
    loss: ProjectParameter = Field(default_factory=ProjectParameter, description="Loss function(s) optimized")
    scheduler: ProjectParameter = Field(default_factory=ProjectParameter, description="Learning rate scheduler")
    input_size: ProjectParameter = Field(default_factory=ProjectParameter, description="Image spatial resolution or input size")
    augmentation: ProjectParameter = Field(default_factory=ProjectParameter, description="Data augmentations applied")
    hardware: ProjectParameter = Field(default_factory=ProjectParameter, description="Compute hardware utilized")
