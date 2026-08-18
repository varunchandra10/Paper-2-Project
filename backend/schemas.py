from pydantic import BaseModel, Field
from typing import List, Dict

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
    rationale: str = Field(description="Brief explanation of the source or logic used to determine this value and confidence level")

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

class PipelineOutput(BaseModel):
    metadata: PaperMetadata = Field(description="Structured metadata of the research paper")
    component_graph: ComponentGraph = Field(description="Structured component graph with gap-filled parameters")

class ComponentFeasibility(BaseModel):
    component_name: str = Field(description="The name of the component being analyzed (e.g., 'Swin Transformer (RFN)')")
    status: str = Field(description="Feasibility status: 'FEASIBLE', 'WARNING', 'IMPOSSIBLE'")
    reason: str = Field(description="Detailed technical reason for the status based on VRAM or compute limitations")
    suggested_substitute: str = Field(description="Actionable suggestion to make it feasible (e.g. LoRA, smaller backbone, freeze)")

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

class Milestone(BaseModel):
    id: int = Field(description="Step sequence number (e.g. 1, 2, 3, etc.)")
    name: str = Field(description="Name of the build milestone (e.g., 'Data Pipeline & Parser Validation')")
    objectives: List[str] = Field(description="Core technical tasks or objectives for this step")
    components_involved: List[str] = Field(description="Names of components built, integrated, or tested in this step")
    estimated_complexity: str = Field(description="Complexity: 'LOW' / 'MEDIUM' / 'HIGH'")
    dependency_rationale: str = Field(description="Explanation of why this step occurs here (e.g., must load dataset before building models, must test locally before scaling)")

class BuildSequence(BaseModel):
    milestones: List[Milestone] = Field(description="Ordered list of build milestones, prioritizing low-cost validation over high-compute training")

class AdaptationReport(BaseModel):
    markdown_content: str = Field(description="The complete synthesized portfolio-grade markdown proposal report including all required sections.")


