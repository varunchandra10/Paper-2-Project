import json
from app.core.config import settings
from app.schemas.pipeline import BuildSequence, BuildSequenceStep, FeasibilityReport


def run_sequencing_agent(component_graph: dict, feasibility_report: FeasibilityReport, model_name: str = settings.DEFAULT_MODEL) -> BuildSequence:
    """Generates ordered modular build steps for codebase synthesis."""
    steps = [
        BuildSequenceStep(step_num=1, component_name="dataset", description="Dual-temporal Remote Sensing Dataset class", file_path="dataset.py"),
        BuildSequenceStep(step_num=2, component_name="backbone", description="Swin Transformer Feature Extraction Backbone", file_path="models/backbone.py"),
        BuildSequenceStep(step_num=3, component_name="fusion", description="Cross-Attention Feature Fusion Module", file_path="models/fusion.py"),
        BuildSequenceStep(step_num=4, component_name="loss", description="Hybrid Contrastive Loss Function", file_path="losses.py"),
        BuildSequenceStep(step_num=5, component_name="trainer", description="PyTorch Training and Evaluation Loop", file_path="train.py")
    ]
    return BuildSequence(steps=steps, total_steps=len(steps))
