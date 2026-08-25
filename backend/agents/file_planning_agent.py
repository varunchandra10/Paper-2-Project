import os
import json
from typing import TypedDict, List, Dict
from langchain_ollama import ChatOllama
from schemas import ProjectSpecification, ProjectTree

class FilePlanningState(TypedDict):
    project_specification: ProjectSpecification
    project_tree: ProjectTree

def run_file_planning_agent(
    specification: ProjectSpecification,
    model_name: str = "qwen2.5-coder:1.5b"
) -> ProjectTree:
    """Uses Ollama structured output to translate ProjectSpecification into a modular ProjectTree

    specifying target directories, files, and tree structure visualization.
    """
    llm = ChatOllama(model=model_name, temperature=0.0, num_ctx=4096, num_predict=1024)
    structured_llm = llm.with_structured_output(ProjectTree)

    prompt = (
        "You are a Senior Principal Software Architect. Your task is to design the file blueprint layout (Project Tree) "
        "for implementing a remote sensing deep learning change detection project based on the following Specification:\n\n"
        "--- PROJECT SPECIFICATION ---\n"
        f"Requirements: {specification.requirements}\n"
        f"Architecture: {specification.architecture}\n"
        f"Core Components: {', '.join(specification.components)}\n"
        f"Datasets Setup: {', '.join(specification.datasets)}\n"
        f"Training Setup: {specification.training_setup}\n"
        f"Evaluation Metrics: {specification.evaluation}\n"
        f"Applied Adaptations: {', '.join(specification.adaptations)}\n\n"
        "Instructions:\n"
        "1. Populate all fields of the ProjectTree schema model:\n"
        "   - directories: List the relative folder directory paths (e.g. ['data', 'models', 'training', 'evaluation', 'configs']).\n"
        "   - files: Map relative filepaths to their engineering summaries describing the classes, modules, or tools to be implemented.\n"
        "   - tree_structure: Generate a clean ASCII folder hierarchy visualization showing directories and files.\n"
        "2. Ensure the layout is modular: dataset loaders, visual backbone model loaders, fusion adapters, segmentation decoders, losses, trainer, and evaluation utilities should reside in their respective directories."
    )

    print("Sending request to local Ollama for project file planning...")
    try:
        project_tree = structured_llm.invoke(prompt)
    except Exception as e:
        print(f"Warning: File planning agent LLM call failed ({e}). Returning baseline project tree layout.")
        # Baseline fallback project tree layout
        fallback_dirs = ["data", "models", "training", "evaluation", "configs"]
        fallback_files = {
            "data/dataset.py": "Custom PyTorch Dataset class parsing bi-temporal image pairs and change masks for LEVIR-CD.",
            "models/backbone.py": "Utility to load visual backbone encoders (Swin/ResNet) and extract high-level feature maps.",
            "models/fusion.py": "Implements Side Fusion Networks or adapter modules to integrate temporal features.",
            "models/decoder.py": "Decodes fused features into spatial binary change predictions mask.",
            "training/loss.py": "Custom loss function implementations combining Binary Cross Entropy (BCE) and Dice Loss.",
            "training/trainer.py": "FP16 training executor with gradient accumulation steps and validation logic.",
            "evaluation/evaluator.py": "Batch evaluation loops computing IoU and F1-Score metrics.",
            "configs/config.json": "Refinement config parameters registry (e.g. batch size 4, gradient accumulation 4).",
            "requirements.txt": "Package dependency specification tree file.",
            "README.md": "Technical architecture description, usage scripts guide, and spec tree overview."
        }
        fallback_tree = (
            "project/\n"
            "├── data/\n"
            "│   └── dataset.py\n"
            "├── models/\n"
            "│   ├── backbone.py\n"
            "│   ├── fusion.py\n"
            "│   └── decoder.py\n"
            "├── training/\n"
            "│   ├── loss.py\n"
            "│   └── trainer.py\n"
            "├── evaluation/\n"
            "│   └── evaluator.py\n"
            "├── configs/\n"
            "│   └── config.json\n"
            "├── requirements.txt\n"
            "└── README.md"
        )
        project_tree = ProjectTree(
            directories=fallback_dirs,
            files=fallback_files,
            tree_structure=fallback_tree
        )
    return project_tree
