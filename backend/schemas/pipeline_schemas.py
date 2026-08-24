from pydantic import BaseModel, Field
from typing import List, Dict, Optional

# Day 1 & Day 2 schemas
class SectionInfo(BaseModel):
    title: str = Field(description="The exact title of the section (e.g., 'I. INTRODUCTION', 'III. METHOD')")
    character_count: int = Field(description="Length of the section content in characters")

class PaperMetadata(BaseModel):
    title: str = Field(description="The official title of the research paper")
    authors: List[str] = Field(description="List of author names extracted from the paper")
    abstract: str = Field(description="The full abstract of the paper")
    sections_found: List[SectionInfo] = Field(description="List of all sections parsed in the paper")
    primary_contribution: str = Field(description="A concise summary (2-3 sentences) of the paper's primary contribution")

# Day 3, 4, 5 schemas (Component Graph & Parameter Details)
class ParameterDetails(BaseModel):
    value: str = Field(description="The extracted value of the parameter (e.g., '24', '0.001', '512', or 'Not specified')")
    confidence: str = Field(description="Confidence tagging: 'CONFIRMED' / 'INFERRED' / 'ASSUMED'")
    rationale: str = Field(default="Not specified", description="Brief explanation of the source or logic used to determine this value and confidence level")

class Component(BaseModel):
    name: str = Field(description="The name of the component, e.g., 'Swin Transformer (RFN)', 'Side Fusion Network (SFN)'")
    type: str = Field(description="The category of the component. Must be one of: 'encoder', 'fusion', 'decoder', 'loss', 'training'")
    description: str = Field(description="A brief description of what this component does in the paper's architecture")
    inputs: List[str] = Field(description="List of input data streams, feature maps, or tensors it accepts")
    outputs: List[str] = Field(description="List of outputs or tensors it produces")
    parameters: Dict[str, ParameterDetails] = Field(
        description="Mapping of hyperparameter names to their detailed values, confidence tags, and rationales"
    )

class ComponentGraph(BaseModel):
    components: List[Component] = Field(description="List of all structural architecture components extracted from the paper")
    edges: List[Dict[str, str]] = Field(
        default_factory=list, 
        description="Directed data flow edges connecting components, e.g. [{'source': 'Visual Encoder', 'target': 'Swin Transformer Decoder'}]"
    )

class PipelineOutput(BaseModel):
    metadata: PaperMetadata = Field(description="Structured metadata of the research paper")
    component_graph: ComponentGraph = Field(description="Structured component graph with gap-filled parameters")

class ComponentFeasibility(BaseModel):
    component_name: str = Field(description="The name of the component being analyzed (e.g., 'Swin Transformer (RFN)')")
    status: str = Field(description="Feasibility status: 'FEASIBLE', 'WARNING', 'IMPOSSIBLE'")
    reason: str = Field(description="One-sentence technical reason for the status (max 80 words). Do NOT repeat yourself.")
    suggested_substitute: str = Field(description="One concrete actionable suggestion (e.g. LoRA, smaller backbone, freeze layers). Max 30 words.")

class AlternativePlatform(BaseModel):
    platform_name: str = Field(description="Name of the cloud platform (e.g. 'Google Colab', 'Kaggle Kernels', 'Groq API', 'RunPod')")
    description: str = Field(description="Brief details of what this platform offers (e.g. free GPU, free credits, LPU speed)")
    how_to_use: str = Field(description="Actionable step-by-step guidance on how to run this project on this platform")

class FeasibilityReport(BaseModel):
    overall_status: str = Field(description="Overall project feasibility status: 'FEASIBLE', 'WARNING', 'IMPOSSIBLE'")
    components_analysis: List[ComponentFeasibility] = Field(description="List of feasibility analysis reports for each component")
    training_status: str = Field(description="Training regime feasibility status: 'FEASIBLE', 'WARNING', 'IMPOSSIBLE'")
    training_reason: str = Field(description="Detailed reason for the training status based on timeline and epoch calculations")
    training_substitute: str = Field(description="Suggested swap for training parameters (e.g. reduce batch size, use gradient accumulation)")
    recommendations: List[str] = Field(description="Actionable summary of recommendations to compile the project")
    alternatives: List[AlternativePlatform] = Field(description="List of free or low-cost alternative cloud platforms with setup guidance")

    @property
    def components(self) -> List[ComponentFeasibility]:
        return self.components_analysis


class Milestone(BaseModel):
    id: int = Field(description="Step sequence number (e.g. 1, 2, 3, etc.)")
    name: str = Field(description="Name of the build milestone (e.g., 'Data Pipeline & Parser Validation')")
    objectives: List[str] = Field(description="Core technical tasks or objectives for this step")
    components_involved: List[str] = Field(description="Names of components built, integrated, or tested in this step")
    estimated_complexity: str = Field(description="Complexity: 'LOW' / 'MEDIUM' / 'HIGH'")
    estimated_duration_days: int = Field(default=3, description="Estimated number of days to complete this milestone (e.g. 2, 5, 7)")
    priority: str = Field(default="MEDIUM", description="Priority level: 'LOW' / 'MEDIUM' / 'HIGH' / 'CRITICAL'")
    dependency_rationale: str = Field(description="Explanation of why this step occurs here (max 50 words). Do NOT repeat yourself.")

class BuildSequence(BaseModel):
    milestones: List[Milestone] = Field(description="Ordered list of build milestones, prioritizing low-cost validation over high-compute training")
    total_duration_weeks: float = Field(default=0.0, description="Total estimated project duration in weeks (sum of all milestone days / 7)")

class AdaptationReport(BaseModel):
    executive_summary: str = Field(default="", description="Executive summary paragraph")
    bottleneck_analysis: str = Field(default="", description="ML systems bottleneck analysis")
    cloud_migration_guide: str = Field(default="", description="Cloud platform migration guide")
    markdown_content: str = Field(description="The complete synthesized portfolio-grade markdown proposal report including all required sections.")


class ProjectParameter(BaseModel):
    value: str = Field(description="The extracted parameter value (e.g., 'AdamW', '0.001', 'LEVIR-CD', '512x512', or 'Not specified')")
    source: str = Field(description="Exact source location in the paper, e.g., 'Section III-A, Page 4'")
    status: str = Field(description="Provenance status: 'EXPLICIT', 'INFERRED', 'ASSUMED', 'DERIVED', 'UNKNOWN'")
    confidence: float = Field(description="Confidence rating from 0.0 to 1.0 based on provenance hierarchy")

class ExtractedParameters(BaseModel):
    model: ProjectParameter = Field(description="Model architecture/backbone name")
    dataset: ProjectParameter = Field(description="Dataset used for evaluation/training")
    optimizer: ProjectParameter = Field(description="Optimization algorithm used")
    learning_rate: ProjectParameter = Field(description="Base learning rate parameter")
    batch_size: ProjectParameter = Field(description="Training batch size")
    epochs: ProjectParameter = Field(description="Number of training epochs")
    loss: ProjectParameter = Field(description="Loss function(s) optimized")
    scheduler: ProjectParameter = Field(description="Learning rate scheduler")
    input_size: ProjectParameter = Field(description="Image spatial resolution or input size")
    augmentation: ProjectParameter = Field(description="Data augmentations applied during training")
    hardware: ProjectParameter = Field(description="Compute hardware utilized for training/experiments")

class ParameterGap(BaseModel):
    parameter_name: str = Field(description="Name of the parameter (e.g. 'learning_rate', 'batch_size', 'gpu', 'preprocessing')")
    classification: str = Field(description="Classification status: 'EXPLICIT', 'DERIVABLE', 'MISSING', 'AMBIGUOUS'")
    value: str = Field(description="The extracted or resolved parameter value")
    details: str = Field(description="Technical rationale or search source for this classification and value")

class GapReport(BaseModel):
    parameter_gaps: List[ParameterGap] = Field(description="Detailed classification list of all critical project parameters")
    has_critical_missing_parameters: bool = Field(description="Flag indicating if any parameters classified as MISSING are blocking development")
    summary: str = Field(description="A brief summary explaining the state of parameter gaps and action plan to resolve them")
