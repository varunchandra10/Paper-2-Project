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
