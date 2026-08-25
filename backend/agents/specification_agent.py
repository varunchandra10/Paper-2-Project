import os
import json
from typing import TypedDict
from langchain_ollama import ChatOllama
from schemas import ComponentGraph, FeasibilityReport, BuildSequence, ProjectSpecification

class SpecificationState(TypedDict):
    component_graph: ComponentGraph
    feasibility_report: FeasibilityReport
    build_sequence: BuildSequence
    project_specification: ProjectSpecification

def run_specification_agent(
    component_graph: ComponentGraph,
    feasibility_report: FeasibilityReport,
    build_sequence: BuildSequence,
    model_name: str = "qwen2.5-coder:1.5b"
) -> ProjectSpecification:
    """Uses Ollama structured output to translate component graph, feasibility limits, and build sequence milestones
    into a detailed, standard ProjectSpecification code-blueprint.
    """
    llm = ChatOllama(model=model_name, temperature=0.0, num_ctx=4096, num_predict=1024)
    structured_llm = llm.with_structured_output(ProjectSpecification)

    prompt = (
        "You are an expert Machine Learning Systems Engineer. Your task is to compile a formal, structured ProjectSpecification "
        "document (ML systems blueprint) from the provided Component Graph, Feasibility Report, and engineering Build Milestones Sequence.\n\n"
        "--- COMPONENT GRAPH ---\n"
        f"{json.dumps(component_graph.model_dump(), indent=2)}\n\n"
        "--- FEASIBILITY REPORT ---\n"
        f"{json.dumps(feasibility_report.model_dump(), indent=2)}\n\n"
        "--- BUILD SEQUENCE MILESTONES ---\n"
        f"{json.dumps(build_sequence.model_dump(), indent=2)}\n\n"
        "Instructions:\n"
        "1. Populate all fields of the ProjectSpecification model with professional, engineering-grade details:\n"
        "   - requirements: Detail specific target libraries (e.g. PyTorch, PyMuPDF, etc.), CUDA drivers version, and VRAM limits.\n"
        "   - architecture: Present a clear sequence flow explanation of inputs/outputs mapping from backbone encoders to fusion and decoder layers.\n"
        "   - components: List specific file/class names that must be implemented (e.g. ['SwinBackbone', 'SideFusionNetwork', 'LossFunctions', 'Trainer']).\n"
        "   - dependencies: List file compiler dependencies or import chains in sequence.\n"
        "   - datasets: Specify dataloader properties, patch crop sizes (e.g. 128x128), and LEVIR-CD train/val/test divisions.\n"
        "   - training_setup: Detail epochs, loss functions, learning rate, and optimizer. Highlight gradient accumulation (e.g. 4) and FP16 usage.\n"
        "   - evaluation: Specify convergence validation frequency, F1-Score / IoU calculations, and checkpoint save locations.\n"
        "   - assumptions: List hardware limits (e.g. RTX 5050 Laptop GPU, 8GB VRAM) and dataset path availability.\n"
        "   - adaptations: Highlight all hyperparameter overrides and trace origins (e.g. PAPER ORIGINAL: 16 vs HARDWARE ADAPTATION: 4 for batch size).\n"
    )

    print("Sending request to local Ollama for project specification...")
    try:
        specification = structured_llm.invoke(prompt)
    except Exception as e:
        print(f"Warning: Project specification agent LLM call failed ({e}). Returning baseline project specification.")
        # Baseline fallback project specification
        components_list = [comp.name for comp in component_graph.components] if component_graph.components else ["Visual Encoder", "Adapter Fusion Network", "Change Decoder"]
        
        # Pull any adaptations from component graph parameters
        adaptations_list = []
        if component_graph:
            for comp in component_graph.components:
                for pk, pv in comp.parameters.items():
                    if "PAPER ORIGINAL" in pv.rationale:
                        adaptations_list.append(f"{comp.name} - {pk.upper()}: {pv.value} ({pv.rationale})")
        if not adaptations_list:
            adaptations_list = [
                "BATCH_SIZE: 4 (PAPER ORIGINAL: 16 vs HARDWARE ADAPTATION: 4 reduced to fit local VRAM limits)",
                "FREEZE_BACKBONE: True (PAPER ORIGINAL: False vs HARDWARE ADAPTATION: True to save gradients memory)"
            ]

        specification = ProjectSpecification(
            requirements="Python 3.10+, PyTorch 2.0+, CUDA 11.8+, psutil, numpy, scikit-learn. Host VRAM target limit: 8.0 GB.",
            architecture="Unified change detection flow: Bi-temporal image patches ➔ Visual backbones feature extraction ➔ Adaptive Fusion Network ➔ Change Decoder ➔ Binary output change mask.",
            components=components_list,
            dependencies=[f"{c} depends on previous data pipeline loader outputs" for c in components_list],
            datasets=["LEVIR-CD dataset custom patches loader.", "Crop patch dimensions: 128x128 pixels.", "Train / Val / Test division setup."],
            training_setup="Optimizer: AdamW | Base Learning Rate: 0.0001 | Loss: Binary Cross BCE + Dice Loss | Mixed Precision: FP16 Enabled | Gradient Accumulation: 4 steps.",
            evaluation="Validation Frequency: Every 1 epoch | Primary Metrics: F1-Score, IoU | Checkpointer: Save best weights based on val IoU.",
            assumptions=["Host hardware matches RTX 5050 Laptop GPU or equivalent.", "LEVIR-CD raw files are stored in accessible directories.", "Pre-trained visual encoder weights are initialized locally."],
            adaptations=adaptations_list
        )
    return specification
