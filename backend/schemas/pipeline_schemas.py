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
    overall_status: str = Field(description="Overall project feasibility status: 'FEASIBLE', 'FEASIBLE_WITH_MODIFICATION', 'NOT_FEASIBLE', 'UNKNOWN'")
    components_analysis: List[ComponentFeasibility] = Field(description="List of feasibility analysis reports for each component")
    training_status: str = Field(description="Training regime feasibility status: 'FEASIBLE', 'FEASIBLE_WITH_MODIFICATION', 'NOT_FEASIBLE', 'UNKNOWN'")
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

class CPUProfile(BaseModel):
    processor_name: str = Field(description="CPU model/processor name")
    physical_cores: int = Field(description="Number of physical CPU cores")
    logical_cores: int = Field(description="Number of logical CPU cores")
    frequency_mhz: float = Field(default=0.0, description="CPU clock speed frequency in MHz")
    usage_pct: float = Field(description="Current CPU usage percentage")

class RAMProfile(BaseModel):
    total_gb: float = Field(description="Total system RAM in GB")
    available_gb: float = Field(description="Available system RAM in GB")
    used_gb: float = Field(description="Used system RAM in GB")
    usage_pct: float = Field(description="System RAM usage percentage")

class GPUProfile(BaseModel):
    name: str = Field(description="GPU model/device name")
    driver_version: str = Field(default="Unknown", description="NVIDIA driver version")
    cuda_version: str = Field(default="Unknown", description="System CUDA version support")
    vram_total_gb: float = Field(description="Total VRAM in GB")
    vram_free_gb: float = Field(description="Free VRAM in GB")
    vram_used_gb: float = Field(description="Used VRAM in GB")
    temperature_c: float = Field(default=-1.0, description="GPU temperature in Celsius")

class DiskProfile(BaseModel):
    path: str = Field(description="Absolute path of the drive profiled")
    total_gb: float = Field(description="Total disk space in GB")
    free_gb: float = Field(description="Free disk space in GB")
    used_gb: float = Field(description="Used disk space in GB")
    usage_pct: float = Field(description="Disk space usage percentage")

class OSProfile(BaseModel):
    system: str = Field(description="OS system platform (e.g. Windows, Linux, Darwin)")
    release: str = Field(description="OS release version")
    version: str = Field(description="Detailed OS version string")
    machine: str = Field(description="System hardware/machine architecture (e.g. AMD64, x86_64)")

class PythonProfile(BaseModel):
    version: str = Field(description="Python version string")
    executable: str = Field(description="Path to active Python executable")
    in_virtualenv: bool = Field(description="Flag indicating if python runs in a virtual environment")
    package_versions: Dict[str, str] = Field(default_factory=dict, description="Dictionary of key packages and their installed versions")

class HardwareProfile(BaseModel):
    cpu: CPUProfile = Field(description="CPU hardware profile specs")
    ram: RAMProfile = Field(description="System RAM profile specs")
    gpus: List[GPUProfile] = Field(default_factory=list, description="List of detected GPUs profile specs")
    disk: DiskProfile = Field(description="Disk storage profile specs")
    os: OSProfile = Field(description="Operating System profile specs")
    python: PythonProfile = Field(description="Python runtime environment specs")
    timestamp: str = Field(description="ISO-formatted timestamp when the profile was generated")

class ModelResourceRequirement(BaseModel):
    param_count_millions: float = Field(description="Estimated parameter count in millions")
    model_weights_mb: float = Field(description="Estimated model weights footprint in MB")
    vram_minimum_gb: float = Field(description="Minimum VRAM required to load weights in GB")
    description: str = Field(description="Detailed architecture and weights footprint assessment")

class DatasetResourceRequirement(BaseModel):
    raw_size_gb: float = Field(description="Estimated raw dataset footprint in GB")
    sample_count: int = Field(description="Estimated sample count/images in dataset")
    description: str = Field(description="Dataset sample and layout analysis")

class TrainingResourceRequirement(BaseModel):
    vram_recommended_gb: float = Field(description="Minimum recommended GPU VRAM in GB for training forward/backward passes")
    ram_recommended_gb: float = Field(description="Minimum recommended system RAM in GB for training load")
    estimated_time_hours: float = Field(description="Estimated training time in hours on system hardware")
    description: str = Field(description="Training load, VRAM allocations, and compute analysis")

class InferenceResourceRequirement(BaseModel):
    vram_gb: float = Field(description="Estimated VRAM required for active inference in GB")
    ram_gb: float = Field(description="Estimated system RAM required for active inference in GB")
    latency_ms: float = Field(description="Estimated inference batch latency in milliseconds")
    description: str = Field(description="Inference deployment spec and speed estimation")

class StorageResourceRequirement(BaseModel):
    required_disk_gb: float = Field(description="Estimated total disk space in GB required for dataset, logs, and checkpoints")
    description: str = Field(description="Total disk space allocations breakdown")

class ResourceEstimationReport(BaseModel):
    model: ModelResourceRequirement = Field(description="Model memory and structure specifications")
    dataset: DatasetResourceRequirement = Field(description="Dataset storage and structure specifications")
    training: TrainingResourceRequirement = Field(description="Training resource allocation specs")
    inference: InferenceResourceRequirement = Field(description="Inference deployment resource specs")
    storage: StorageResourceRequirement = Field(description="Disk storage resource footprint specs")
    overall_resource_tier: str = Field(description="Overall complexity/resource tier: 'LOW' / 'MEDIUM' / 'HIGH' / 'EXTREME'")


class ProjectSpecification(BaseModel):
    requirements: str = Field(description="System requirements, CUDA version, packages, VRAM limits, etc.")
    architecture: str = Field(description="Overview of the network architecture (e.g. encoders, bridge adapters, fusion, decoders).")
    components: List[str] = Field(description="Names of components/modules that will be implemented as separate code units.")
    dependencies: List[str] = Field(description="Ordered compilation dependencies showing component sequence flow.")
    datasets: List[str] = Field(description="Dataset structures, sample dimensions, data loaders config, and splits.")
    training_setup: str = Field(description="Training configuration including epochs, batch size, learning rate, loss functions, optimizer, gradient accumulation, mixed precision, and frozen components.")
    evaluation: str = Field(description="Evaluation metrics, inference verification pipelines, validation frequency, and visual checkpointers.")
    assumptions: List[str] = Field(description="Key assumptions about data availability, hardware configurations, and hyperparameter choices.")
    adaptations: List[str] = Field(description="Detailed list of all applied hardware adaptations, tracing originals to modified settings (e.g. reduced batch sizes).")


class ProjectTree(BaseModel):
    directories: List[str] = Field(description="List of target directory paths to create in the workspace.")
    files: Dict[str, str] = Field(description="Mapping of relative filepaths to their descriptive engineering summaries.")
    tree_structure: str = Field(description="Visual ASCII/Markdown representation of the project folder tree hierarchy.")




